"""Protocol-neutral public contracts and built-in adapters."""
from .a2a import A2AServerProtocolAdapter
from .base import (
    ProtocolConfiguration,
    ProtocolRole,
    ProtocolType,
    ServerProtocolAdapter,
)
from .registry import ProtocolAdapterRegistry

__all__ = [
    "A2AServerProtocolAdapter",
    "ProtocolAdapterRegistry",
    "ProtocolConfiguration",
    "ProtocolRole",
    "ProtocolType",
    "ServerProtocolAdapter",
]
