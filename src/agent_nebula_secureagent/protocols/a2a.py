"""A2A implementation of the protocol-neutral SecureAgent server contract."""
from __future__ import annotations

from dataclasses import dataclass
import inspect
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

        SecureAgent only adapts its protocol-neutral ``SkillDefinition`` objects
        to Platform's A2A executable-skill contract. Platform owns Agent Card
        validation, the Agent Nebula skill-selection extension, deterministic
        dispatch, security enforcement, and official A2A request handling.
        """
        executable_skills = tuple(_A2AExecutableSkill(skill) for skill in skills)
        return A2AStandaloneApplicationComposer().compose(
            application_config=application_config,
            server_config=protocol_config,
            skills=executable_skills,
            nebula_config=nebula_config,
        )
