"""SecureAgent composition of a native A2A server."""
from __future__ import annotations

from collections.abc import Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import uvicorn
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from fastapi import FastAPI

from agent_nebula_platform.a2a import A2ASdkServerAdapter
from agent_nebula_platform.a2a.config import (
    A2AListenerConfigurationLoader,
    A2AServerConfigurationService,
)
from agent_nebula_platform.a2a.extensions import (
    ensure_schema_contract_extension,
    ensure_skill_selection_extension,
    selected_skill_id,
    validate_executable_skills,
)
from agent_nebula_platform.a2a.security import A2AServerSecurityFactory
from agent_nebula_platform.a2a.security.server import (
    A2AConfiguredSecurityLoader,
    A2AServerSecurityService,
)

from ..logging import SecureAgentLoggingConfiguration, create_uvicorn_log_config


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

    def __init__(
        self,
        skills: tuple[A2AExecutableSkill, ...],
        security: A2AServerSecurityService,
    ) -> None:
        self._skills = {skill.skill_id: skill.executor for skill in skills}
        self._security = security
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

        # A2A authentication happens at HTTP ingress when the applicable
        # AgentCard requirement is already known. AgentSkill requirements cannot
        # be enforced there: the selected skill is carried by the Nebula
        # skill-selection extension and is resolved only from RequestContext.
        # Authorize the resolved skill here, before any application executor runs.
        self._security.authorize_skill(
            skill_id=skill_id,
            call_context=context.call_context,
        )

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
        logging: SecureAgentLoggingConfiguration,
    ) -> None:
        server = A2AServerConfigurationService().load(configuration_file)
        listener = A2AListenerConfigurationLoader().load(configuration_file)
        validate_executable_skills(server.agent_card, tuple(skill.skill_id for skill in skills))
        ensure_skill_selection_extension(server.agent_card, required=False)
        ensure_schema_contract_extension(server.agent_card, skills)

        authenticators = A2AConfiguredSecurityLoader().load(
            configuration_file,
            mtls_transport_enforced=listener.tls.require_client_certificate,
        )
        self._security = A2AServerSecurityFactory().create(
            agent_card=server.agent_card,
            trust_bundle_file=listener.trust_bundle_file,
            authenticators=authenticators,
        )
        handler = DefaultRequestHandler(
            agent_executor=_SkillDispatcher(skills, self._security.service),
            task_store=InMemoryTaskStore(),
            agent_card=server.agent_card,
        )
        self._adapter: A2ASdkServerAdapter | None = None

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            del app
            assert self._adapter is not None
            await self._adapter.start()
            try:
                yield
            finally:
                await self._adapter.close()

        self._app = FastAPI(lifespan=lifespan)
        self._adapter = A2ASdkServerAdapter(
            app=self._app,
            agent_card=server.agent_card,
            agent_card_route=server.agent_card_route,
            request_handler=handler,
            security=self._security.service,
            tls=listener.tls,
        )
        self._listener = listener
        self._logging = logging

    @property
    def application(self) -> FastAPI:
        return self._app

    def run(self) -> None:
        tls = self._listener.tls
        uvicorn.run(
            self._app,
            host=self._listener.host,
            port=self._listener.port,
            ssl_certfile=str(tls.certificate_file) if tls.enabled else None,
            ssl_keyfile=str(tls.private_key_file) if tls.enabled else None,
            ssl_ca_certs=str(tls.trust_bundle) if tls.enabled and tls.trust_bundle else None,
            ssl_cert_reqs=2 if tls.require_client_certificate else 0,
            log_config=create_uvicorn_log_config(
                self._logging,
                application_loggers=("agent_nebula_platform",),
            ),
            access_log=self._logging.console_logging,
            log_level=self._logging.log_level.lower(),
        )
