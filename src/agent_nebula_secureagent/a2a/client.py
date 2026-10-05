"""SecureAgent construction of native A2A clients."""
from __future__ import annotations

from pathlib import Path

from a2a.client import Client
from a2a.types import AgentCard
from agent_nebula_platform.a2a import A2AClient
from agent_nebula_platform.a2a.config import A2AClientConfigurationLoader
from agent_nebula_platform.a2a.security import (
    A2AClientSecurityInterceptor,
    A2AClientSecurityResolver,
)
from agent_nebula_platform.a2a.security.client import (
    A2AApiKeyCredentialProvider,
    A2ADiscoveredOAuth2CredentialProvider,
    A2AHttpCredentialProvider,
    A2AMutualTlsCredentialProvider,
    A2AOidcCredentialProvider,
    load_static_credentials,
)


class SecureAgentA2AClient:
    """Apply external configuration and expose native ``a2a-sdk`` clients."""

    def __init__(self, configuration_file: Path) -> None:
        configuration = A2AClientConfigurationLoader().load(configuration_file)
        credentials = load_static_credentials(configuration)
        providers = [
            A2AApiKeyCredentialProvider(credentials),
            A2AHttpCredentialProvider(credentials),
            A2AOidcCredentialProvider(credentials),
            A2AMutualTlsCredentialProvider(
                identity_configured=configuration.tls.certificate_file is not None
            ),
        ]
        if configuration.oauth is not None:
            providers.append(
                A2ADiscoveredOAuth2CredentialProvider(
                    configuration=configuration.oauth,
                    tls=configuration.tls,
                    timeout_seconds=configuration.timeout_seconds,
                )
            )
        self._security = A2AClientSecurityInterceptor(
            A2AClientSecurityResolver(tuple(providers))
        )
        self._client = A2AClient(configuration, security=self._security)

    async def resolve_agent_card(self, location: str) -> AgentCard:
        return await self._client.resolve_agent_card(location)

    async def connect(self, location: str) -> Client:
        return await self._client.connect(location)

    async def close(self) -> None:
        await self._security.close()
