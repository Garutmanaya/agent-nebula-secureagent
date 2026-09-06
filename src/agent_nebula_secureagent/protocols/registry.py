"""Registry for protocol implementations available to the SecureAgent facade."""
from __future__ import annotations

from agent_nebula_secureagent.exceptions import SecureAgentProtocolError
from agent_nebula_secureagent.protocols.base import ProtocolType, ServerProtocolAdapter


class ProtocolAdapterRegistry:
    """Store server adapters without coupling SecureAgent to protocol internals."""

    def __init__(self, adapters: tuple[ServerProtocolAdapter, ...] = ()) -> None:
        """Create a registry and reject duplicate protocol implementations."""
        self._adapters: dict[ProtocolType, ServerProtocolAdapter] = {}
        for adapter in adapters:
            self.register(adapter)

    def register(self, adapter: ServerProtocolAdapter) -> None:
        """Register one adapter.

        Args:
            adapter: Concrete protocol adapter to register.

        Raises:
            SecureAgentProtocolError: If an adapter already owns the protocol.
        """
        if adapter.protocol in self._adapters:
            raise SecureAgentProtocolError(
                f"Protocol adapter is already registered: {adapter.protocol.value}"
            )
        self._adapters[adapter.protocol] = adapter

    def require_server(self, protocol: ProtocolType) -> ServerProtocolAdapter:
        """Return the server adapter for a protocol or fail explicitly."""
        adapter = self._adapters.get(protocol)
        if adapter is None:
            raise SecureAgentProtocolError(
                f"Server protocol is not available in Agent Nebula Platform: {protocol.value}"
            )
        return adapter
