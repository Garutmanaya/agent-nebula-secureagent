"""Protocol-neutral contracts used by the SecureAgent facade."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

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
    """Configuration files associated with one protocol role.

    Args:
        protocol: Protocol implementation selected for this configuration.
        role: Whether the configuration exposes a server or creates a client.
        configuration_file: Protocol-owned configuration file.
    """

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
    ) -> SecureAgentApplication:
        """Compose a Platform-owned server from facade-owned business definitions."""
