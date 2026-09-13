"""Protocol-neutral contracts used by the SecureAgent facade."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from agent_nebula_platform.skills import SkillDefinition


class ProtocolType(StrEnum):
    """Protocols addressable through the public SecureAgent interface."""

    A2A = "a2a"
    MCP = "mcp"
    REST = "rest"


class ProtocolRole(StrEnum):
    """Direction in which a SecureAgent uses a protocol."""

    SERVER = "server"
    CLIENT = "client"


@dataclass(frozen=True, slots=True)
class ProtocolConfiguration:
    """Configuration files associated with one protocol role."""

    protocol: ProtocolType
    role: ProtocolRole
    configuration_file: Path


class SecureAgentApplication(Protocol):
    """Minimal lifecycle contract returned by a server protocol adapter."""

    def run(self) -> None:
        """Run the composed server application until shutdown."""

    async def close(self) -> None:
        """Release resources owned by the composed application."""


class ServerProtocolAdapter(ABC):
    """Extension point that maps protocol-neutral skills to a Platform server."""

    @property
    @abstractmethod
    def protocol(self) -> ProtocolType:
        """Return the protocol implemented by this adapter."""

    @abstractmethod
    def compose(
        self,
        *,
        application_config: Path,
        protocol_config: Path,
        nebula_config: Path | None,
        skills: tuple[SkillDefinition, ...],
        a2ui_config: Path | None = None,
    ) -> SecureAgentApplication:
        """Compose a Platform-owned server from facade-owned business definitions."""


class ClientProtocolAdapter(ABC):
    """Protocol-neutral outbound invocation contract implemented through Platform.

    The contract intentionally uses plain mappings and scalar values. Official
    protocol wire models remain owned by Agent Nebula Platform and its protocol SDK.
    """

    @property
    @abstractmethod
    def protocol(self) -> ProtocolType:
        """Return the protocol implemented by this adapter."""

    @abstractmethod
    async def resolve_remote(self, *, protocol_config: Path, target: str) -> Mapping[str, Any]:
        """Resolve protocol discovery metadata for a remote endpoint."""

    @abstractmethod
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
        """Send one protocol message without exposing protocol wire models."""

    @abstractmethod
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
        context_id: str | None = None,
        task_id: str | None = None,
        skill_id: str | None = None,
        a2ui_config: Path | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Send one protocol-neutral A2UI renderer action."""
