"""Registry for protocol implementations available to the SecureAgent facade."""
from __future__ import annotations

from agent_nebula_secureagent.exceptions import SecureAgentProtocolError
from agent_nebula_secureagent.protocols.base import (
    ClientProtocolAdapter,
    ProtocolType,
    ServerProtocolAdapter,
)


class ProtocolAdapterRegistry:
    """Store role-specific adapters without coupling SecureAgent to protocol internals."""

    def __init__(
        self,
        server_adapters: tuple[ServerProtocolAdapter, ...] = (),
        client_adapters: tuple[ClientProtocolAdapter, ...] = (),
    ) -> None:
        self._server_adapters: dict[ProtocolType, ServerProtocolAdapter] = {}
        self._client_adapters: dict[ProtocolType, ClientProtocolAdapter] = {}
        for adapter in server_adapters:
            self.register_server(adapter)
        for adapter in client_adapters:
            self.register_client(adapter)

    def register(self, adapter: ServerProtocolAdapter) -> None:
        """Backward-compatible alias for registering a server adapter."""
        self.register_server(adapter)

    def register_server(self, adapter: ServerProtocolAdapter) -> None:
        """Register one server adapter."""
        if adapter.protocol in self._server_adapters:
            raise SecureAgentProtocolError(
                f"Server protocol adapter is already registered: {adapter.protocol.value}"
            )
        self._server_adapters[adapter.protocol] = adapter

    def register_client(self, adapter: ClientProtocolAdapter) -> None:
        """Register one client adapter independently of the server implementation."""
        if adapter.protocol in self._client_adapters:
            raise SecureAgentProtocolError(
                f"Client protocol adapter is already registered: {adapter.protocol.value}"
            )
        self._client_adapters[adapter.protocol] = adapter

    @property
    def client_adapters(self) -> tuple[ClientProtocolAdapter, ...]:
        """Return registered client adapters for facade-owned lifecycle cleanup."""
        return tuple(self._client_adapters.values())

    def require_server(self, protocol: ProtocolType) -> ServerProtocolAdapter:
        """Return the server adapter for a protocol or fail explicitly."""
        adapter = self._server_adapters.get(protocol)
        if adapter is None:
            raise SecureAgentProtocolError(
                f"Server protocol is not available in Agent Nebula Platform: {protocol.value}"
            )
        return adapter

    def require_client(self, protocol: ProtocolType) -> ClientProtocolAdapter:
        """Return the client adapter for a protocol or fail explicitly."""
        adapter = self._client_adapters.get(protocol)
        if adapter is None:
            raise SecureAgentProtocolError(
                f"Client protocol is not available in Agent Nebula Platform: {protocol.value}"
            )
        return adapter
