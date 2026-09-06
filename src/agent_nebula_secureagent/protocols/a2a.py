"""A2A implementation of the protocol-neutral SecureAgent server contract."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_nebula_platform.protocols.a2a.server.composition import (
    A2AStandaloneApplicationComposer,
)
from agent_nebula_platform.skills import SkillDefinition, SkillInvocation, SkillResult

from agent_nebula_secureagent.exceptions import SecureAgentConfigurationError
from agent_nebula_secureagent.protocols.base import ProtocolType, ServerProtocolAdapter


@dataclass(frozen=True, slots=True)
class _A2AExecutableSkill:
    """Adapt one generic Platform skill to the A2A business-handler contract."""

    definition: SkillDefinition

    @property
    def skill_id(self) -> str:
        """Return the stable skill identifier published by the application."""
        return self.definition.skill_id

    @property
    def handler(self):
        """Return an A2A-compatible mapping handler around the generic skill."""
        async def invoke(payload):
            result = self.definition.handler(
                SkillInvocation(skill_id=self.definition.skill_id, payload=dict(payload))
            )
            import inspect
            if inspect.isawaitable(result):
                result = await result
            if not isinstance(result, SkillResult):
                raise SecureAgentConfigurationError(
                    f"Skill '{self.definition.skill_id}' must return SkillResult"
                )
            return result.data
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
    ):
        """Delegate A2A composition, security, Agent Card, and lifecycle to Platform.

        A2A 1.0 SendMessage has no standard skill-id field. The current Platform
        A2A composer therefore requires one unambiguous business skill rather
        than inventing a proprietary routing field.
        """
        if len(skills) != 1:
            raise SecureAgentConfigurationError(
                "The current A2A server composition requires exactly one business skill; "
                "A2A 1.0 SendMessage does not define a standard skill identifier."
            )
        return A2AStandaloneApplicationComposer().compose(
            application_config=application_config,
            server_config=protocol_config,
            skill=_A2AExecutableSkill(skills[0]),
            nebula_config=nebula_config,
        )
