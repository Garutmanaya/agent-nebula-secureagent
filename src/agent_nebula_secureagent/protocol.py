"""Protocol names exposed by the SecureAgent facade.

These enums are protocol-neutral facade values.  They intentionally live
outside the deprecated ``protocols`` package so importing SecureAgent never
loads legacy A2A adapters.
"""

from enum import StrEnum


class ProtocolType(StrEnum):
    """Protocols addressable through the public SecureAgent interface."""

    A2A = "a2a"
    MCP = "mcp"
    REST = "rest"


class ProtocolRole(StrEnum):
    """Direction in which a SecureAgent uses a protocol."""

    SERVER = "server"
    CLIENT = "client"
