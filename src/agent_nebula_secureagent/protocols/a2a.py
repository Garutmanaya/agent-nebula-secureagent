"""A2A implementation of the protocol-neutral SecureAgent server contract."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import inspect
from typing import Any
from pathlib import Path

from agent_nebula_platform.a2ui.configuration import A2UIConfiguration
from agent_nebula_platform.protocols.a2a.client.client_service import A2AClientServiceFactory
from agent_nebula_platform.protocols.a2a.server.composition import (
    A2AStandaloneApplicationComposer,
)
from agent_nebula_platform.protocols.a2a.server.execution import A2UIActionHandler
from agent_nebula_platform.skills import SkillDefinition, SkillInvocation, SkillResult

from agent_nebula_secureagent.exceptions import SecureAgentConfigurationError
from agent_nebula_secureagent.protocols.base import (
    ClientProtocolAdapter,
    ProtocolType,
    ServerProtocolAdapter,
)


@dataclass(frozen=True, slots=True)
class _A2AExecutableSkill:
    """Adapt one generic Platform skill to the A2A business-handler contract."""

    definition: SkillDefinition

    @property
    def skill_id(self) -> str:
        """Return the stable skill identifier published by the application."""
        return self.definition.skill_id

    @property
    def schema_contract_id(self) -> str | None:
        """Expose the protocol-neutral contract identifier to Platform."""
        return self.definition.schema_contract_id

    @property
    def input_schema(self) -> Mapping[str, Any] | None:
        """Expose structured input metadata without constructing A2A models."""
        return self.definition.input_schema

    @property
    def output_schema(self) -> Mapping[str, Any] | None:
        """Expose structured output metadata without constructing A2A models."""
        return self.definition.output_schema

    @property
    def handler(self):
        """Return an A2A-compatible mapping handler around the generic skill."""
        async def invoke(payload):
            result = self.definition.handler(
                SkillInvocation(skill_id=self.definition.skill_id, payload=dict(payload))
            )
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, SkillResult):
                raise SecureAgentConfigurationError(
                    f"Skill '{self.definition.skill_id}' must return SkillResult"
                )
            # Preserve the complete protocol-neutral result. Platform owns
            # transport mapping for business data, metadata, and optional A2UI.
            return result
        return invoke


class A2AServerProtocolAdapter(ServerProtocolAdapter):
    """Compose an official A2A server through Agent Nebula Platform."""

    @property
    def protocol(self) -> ProtocolType:
        """Identify this adapter as A2A."""
        return ProtocolType.A2A

    def compose(
        self,
        *,
        application_config: Path,
        protocol_config: Path,
        nebula_config: Path | None,
        skills: tuple[SkillDefinition, ...],
        a2ui_action_handler: A2UIActionHandler | None = None,
        a2ui_config: Path | None = None,
    ):
        """Delegate A2A composition, security, Agent Card, and lifecycle to Platform.

        SecureAgent only adapts its protocol-neutral ``SkillDefinition`` objects
        to Platform's A2A executable-skill contract. Platform owns Agent Card
        validation, the Agent Nebula skill-selection extension, deterministic
        dispatch, security enforcement, and official A2A request handling.
        """
        executable_skills = tuple(_A2AExecutableSkill(skill) for skill in skills)
        a2ui = A2UIConfiguration.load(a2ui_config) if a2ui_config is not None else None
        return A2AStandaloneApplicationComposer().compose(
            application_config=application_config,
            server_config=protocol_config,
            skills=executable_skills,
            nebula_config=nebula_config,
            a2ui=a2ui,
            a2ui_action_handler=a2ui_action_handler,
        )


class A2AClientProtocolAdapter(ClientProtocolAdapter):
    """Thin SecureAgent bridge to Platform's official A2A client implementation.

    No A2A wire model, transport, security, or extension behavior is implemented
    here. Platform owns those concerns and is verified against ``a2a-sdk``.
    """

    @property
    def protocol(self) -> ProtocolType:
        """Identify this adapter as A2A."""
        return ProtocolType.A2A

    async def resolve_remote(
        self, *, protocol_config: Path, target: str
    ) -> Mapping[str, Any]:
        """Resolve the official Agent Card through Platform."""
        adapter = A2AClientServiceFactory().create(protocol_config)
        try:
            return await adapter.resolve_agent_card_document(target)
        finally:
            await adapter.close()

    async def send_message(
        self,
        *,
        protocol_config: Path,
        target: str,
        text: str | None = None,
        data: Mapping[str, Any] | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        skill_id: str | None = None,
        a2ui_config: Path | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Delegate one message, including optional skill selection, to Platform."""
        a2ui = A2UIConfiguration.load(a2ui_config) if a2ui_config is not None else None
        adapter = A2AClientServiceFactory().create(
            protocol_config,
            a2ui_configuration=a2ui,
        )
        try:
            return await adapter.send_message(
                target,
                text=text,
                data=data,
                context_id=context_id,
                task_id=task_id,
                skill_id=skill_id,
            )
        finally:
            await adapter.close()

    async def send_a2ui_action(
        self,
        *,
        protocol_config: Path,
        target: str,
        name: str,
        surface_id: str,
        source_component_id: str,
        context: Mapping[str, Any] | None = None,
        data_model: Mapping[str, Any] | None = None,
        want_response: bool = False,
        action_id: str | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        a2ui_config: Path | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Delegate an A2UI renderer action to Platform's A2A binding."""
        a2ui = A2UIConfiguration.load(a2ui_config) if a2ui_config is not None else None
        if a2ui is None or not a2ui.enabled:
            raise SecureAgentConfigurationError(
                "send_a2ui_action() requires enabled a2ui_config"
            )
        adapter = A2AClientServiceFactory().create(
            protocol_config, a2ui_configuration=a2ui
        )
        try:
            return await adapter.send_a2ui_action(
                target,
                name=name,
                surface_id=surface_id,
                source_component_id=source_component_id,
                context=context,
                data_model=data_model,
                want_response=want_response,
                action_id=action_id,
                context_id=context_id,
                task_id=task_id,
                )
        finally:
            await adapter.close()
