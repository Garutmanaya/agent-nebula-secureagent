"""SecureAgent composition of a native A2A server."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

import httpx
from typing import Any

from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.tasks.base_push_notification_sender import BasePushNotificationSender
from a2a.server.tasks.inmemory_push_notification_config_store import (
    InMemoryPushNotificationConfigStore,
)

from agent_nebula_platform.a2a.runtime import A2APlatformRuntimeComposer
from agent_nebula_platform.a2a.config import (
    A2AListenerConfigurationLoader,
    A2AServerConfigurationService,
)
from agent_nebula_platform.a2a.extensions import (
    ensure_a2ui_extension,
    ensure_schema_contract_extension,
    ensure_skill_selection_extension,
    selected_skill_id,
    validate_executable_skills,
)
from agent_nebula_platform.a2a.security import (
    A2AAuthorizedRequestHandler,
    A2AServerSecurityFactory,
)
from agent_nebula_platform.a2a.security.server import A2AConfiguredSecurityLoader
from agent_nebula_platform.a2ui.configuration import A2UIConfiguration



@dataclass(frozen=True, slots=True)
class A2AExecutableSkill:
    """Bind one advertised skill identifier to its native SDK executor."""

    skill_id: str
    executor: AgentExecutor
    schema_contract_id: str | None = None
    input_schema: Mapping[str, Any] | None = None
    output_schema: Mapping[str, Any] | None = None


class _SkillDispatcher(AgentExecutor):
    """Dispatch only the Nebula skill-selection extension; execution stays native."""

    def __init__(self, skills: tuple[A2AExecutableSkill, ...]) -> None:
        self._skills = {skill.skill_id: skill.executor for skill in skills}
        self._task_skills: dict[str, str] = {}

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        skill_id = selected_skill_id(
            metadata=context.metadata,
            requested_extensions=context.requested_extensions,
        )
        if skill_id is None:
            if len(self._skills) != 1:
                raise ValueError(
                    "Multi-skill A2A agent requires the Nebula skill-selection extension"
                )
            skill_id = next(iter(self._skills))
        executor = self._skills.get(skill_id)
        if executor is None:
            raise ValueError(f"Selected A2A skill is not registered: {skill_id}")

        # Authentication and skill authorization are complete before a2a-sdk
        # invokes this dispatcher. This class only routes the selected skill to
        # its application AgentExecutor.

        if context.task_id is not None:
            self._task_skills[context.task_id] = skill_id
        await executor.execute(context, event_queue)

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        skill_id = self._task_skills.get(context.task_id or "")
        if skill_id is None and len(self._skills) == 1:
            skill_id = next(iter(self._skills))
        if skill_id is None:
            raise ValueError("Cannot route cancellation without the selected skill")
        try:
            await self._skills[skill_id].cancel(context, event_queue)
        finally:
            if context.task_id is not None:
                self._task_skills.pop(context.task_id, None)


class SecureAgentA2AServer:
    """Compose Platform A2A configuration/security with native SDK execution."""

    def __init__(
        self,
        *,
        configuration_file: Path,
        skills: tuple[A2AExecutableSkill, ...],
        application_config: Path,
        nebula_config: Path | None,
        a2ui_config: Path | None,
    ) -> None:
        server = A2AServerConfigurationService().load(configuration_file)
        listener = A2AListenerConfigurationLoader().load(configuration_file)
        validate_executable_skills(server.agent_card, tuple(skill.skill_id for skill in skills))
        ensure_skill_selection_extension(server.agent_card, required=False)
        ensure_schema_contract_extension(server.agent_card, skills)
        if a2ui_config is not None:
            a2ui = A2UIConfiguration.load(a2ui_config)
            if a2ui.enabled:
                ensure_a2ui_extension(
                    server.agent_card,
                    supported_catalog_ids=a2ui.supported_catalog_ids,
                    accepts_inline_catalogs=a2ui.accepts_inline_catalogs,
                )

        authenticators = A2AConfiguredSecurityLoader().load(
            configuration_file,
            mtls_transport_enforced=listener.tls.require_client_certificate,
        )
        self._security = A2AServerSecurityFactory().create(
            agent_card=server.agent_card,
            trust_bundle_file=listener.trust_bundle_file,
            authenticators=authenticators,
        )
        self._push_http_client: httpx.AsyncClient | None = None
        push_config_store = None
        push_sender = None
        if server.agent_card.capabilities.push_notifications:
            push_config_store = InMemoryPushNotificationConfigStore()
            self._push_http_client = httpx.AsyncClient()
            push_sender = BasePushNotificationSender(
                self._push_http_client,
                push_config_store,
            )

        native_handler = DefaultRequestHandler(
            agent_executor=_SkillDispatcher(skills),
            task_store=InMemoryTaskStore(),
            agent_card=server.agent_card,
            push_config_store=push_config_store,
            push_sender=push_sender,
            extended_agent_card=server.extended_agent_card,
        )
        handler = A2AAuthorizedRequestHandler(
            inner=native_handler,
            agent_card=server.agent_card,
            security=self._security.service,
        )
        # Keep native a2a-sdk request handling, but host it inside the existing
        # Platform Runtime. The Runtime is required for restricted configuration
        # paths and for onboarding, health, metrics, telemetry, state and lifecycle.
        self._runtime = A2APlatformRuntimeComposer().compose(
            application_config=application_config,
            server_config=configuration_file,
            nebula_config=nebula_config,
            server_configuration=server,
            listener=listener,
            request_handler=handler,
            security=self._security,
        )

    @property
    def application(self):
        return self._runtime.app

    def run(self) -> None:
        self._runtime.run()

    async def close(self) -> None:
        await self._runtime.close()
        if self._push_http_client is not None:
            await self._push_http_client.aclose()
