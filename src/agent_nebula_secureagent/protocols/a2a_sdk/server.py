"""SecureAgent adapter for Platform's isolated native ``a2a-sdk`` server path.

This module intentionally does not adapt application execution into
``SkillInvocation``/``SkillResult``.  Registered skills contain a native SDK
``AgentExecutor`` which Platform dispatches without changing RequestContext,
EventQueue, or the events produced by the application.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from a2a.server.agent_execution import AgentExecutor

from agent_nebula_platform.a2ui.configuration import A2UIConfiguration
from agent_nebula_platform.protocols.a2a.server_a2a_sdk.composition import (
    A2ASdkStandaloneApplicationComposer,
)
from agent_nebula_platform.protocols.a2a.server_a2a_sdk.execution import A2UIActionHandler


@dataclass(frozen=True, slots=True)
class A2ASdkExecutableSkill:
    """One Agent Card skill implemented by a native ``a2a-sdk`` executor."""

    skill_id: str
    executor: AgentExecutor
    schema_contract_id: str | None = None
    input_schema: Mapping[str, Any] | None = None
    output_schema: Mapping[str, Any] | None = None


class A2ASdkServerProtocolAdapter:
    """Compose SecureAgent through Platform's isolated native A2A server."""

    def compose(
        self,
        *,
        application_config: Path,
        protocol_config: Path,
        nebula_config: Path | None,
        skills: tuple[A2ASdkExecutableSkill, ...],
        a2ui_action_handler: A2UIActionHandler | None = None,
        a2ui_config: Path | None = None,
    ):
        """Delegate infrastructure composition without adapting SDK execution."""
        a2ui = A2UIConfiguration.load(a2ui_config) if a2ui_config is not None else None
        return A2ASdkStandaloneApplicationComposer().compose(
            application_config=application_config,
            server_config=protocol_config,
            skills=skills,
            nebula_config=nebula_config,
            a2ui=a2ui,
            a2ui_action_handler=a2ui_action_handler,
        )
