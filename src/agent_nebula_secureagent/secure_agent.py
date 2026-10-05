"""Configuration-first developer facade for Agent Nebula SecureAgent."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from a2a.client import Client
from a2a.server.agent_execution import AgentExecutor
from a2a.types import AgentCard
from agent_nebula_platform.integrations.nebula import NebulaDiscoveryServiceFactory

from .a2a import A2AExecutableSkill, SecureAgentA2AClient, SecureAgentA2AServer
from .discovery import DiscoveredAgent, DiscoveryNormalizer
from .exceptions import SecureAgentConfigurationError, SecureAgentSkillRegistrationError
from .logging import SecureAgentLoggingConfiguration, load_logging_configuration


class SecureAgent:
    """Configure Agent Nebula integration while exposing native protocol SDK objects."""

    def __init__(
        self,
        config: str | Path = "secureagent.conf",
        *,
        nebula_config: str | Path | None = None,
        a2ui_config: str | Path | None = None,
        protocol_registry: object | None = None,
    ) -> None:
        # ``a2ui_config`` and ``protocol_registry`` remain accepted only so this
        # migration does not break construction. A2UI and legacy A2A adapters are
        # deliberately not part of the new A2A path.
        del a2ui_config, protocol_registry
        self._application_config = Path(config)
        self._nebula_config = Path(nebula_config) if nebula_config is not None else None
        self._a2a_server_config: Path | None = None
        self._a2a_client_config: Path | None = None
        self._a2a_skills: dict[str, A2AExecutableSkill] = {}
        self._a2a_client_integration: SecureAgentA2AClient | None = None
        self._application: SecureAgentA2AServer | None = None

    @property
    def application(self):
        """Return the composed server application, if any."""
        return self._application.application if self._application is not None else None

    @property
    def logging(self) -> SecureAgentLoggingConfiguration:
        """Return validated console logging settings from ``secureagent.conf``."""
        return load_logging_configuration(self._application_config)

    def use_protocol(
        self,
        protocol: object,
        *,
        role: object = "server",
        config: str | Path,
    ) -> SecureAgent:
        """Configure an A2A client or server from its external configuration file."""
        protocol_name = getattr(protocol, "value", protocol)
        role_name = getattr(role, "value", role)
        if protocol_name != "a2a":
            raise SecureAgentConfigurationError(
                "SA-P2 supports only the migrated A2A protocol path"
            )
        configuration = Path(config)
        if role_name == "server":
            if self._a2a_server_config is not None:
                raise SecureAgentConfigurationError("A2A server is already configured")
            self._a2a_server_config = configuration
        elif role_name == "client":
            if self._a2a_client_config is not None:
                raise SecureAgentConfigurationError("A2A client is already configured")
            self._a2a_client_config = configuration
        else:
            raise SecureAgentConfigurationError(f"Unsupported protocol role: {role_name}")
        return self

    def a2a_skill(
        self,
        skill_id: str,
        executor: AgentExecutor,
        *,
        schema_contract_id: str | None = None,
        input_schema: dict[str, Any] | None = None,
        output_schema: dict[str, Any] | None = None,
    ) -> SecureAgent:
        """Register one advertised A2A skill with its native SDK executor."""
        normalized = skill_id.strip()
        if not normalized:
            raise SecureAgentSkillRegistrationError("Skill identifier must not be blank")
        if normalized in self._a2a_skills:
            raise SecureAgentSkillRegistrationError(
                f"Skill is already registered: {normalized}"
            )
        if not isinstance(executor, AgentExecutor):
            raise SecureAgentSkillRegistrationError(
                f"A2A skill '{normalized}' executor must implement AgentExecutor"
            )
        contract_id = (schema_contract_id or "").strip() or None
        if (input_schema is not None or output_schema is not None) and contract_id is None:
            raise SecureAgentSkillRegistrationError(
                f"Skill '{normalized}' requires schema_contract_id when a schema is declared"
            )
        self._a2a_skills[normalized] = A2AExecutableSkill(
            skill_id=normalized,
            executor=executor,
            schema_contract_id=contract_id,
            input_schema=dict(input_schema) if input_schema is not None else None,
            output_schema=dict(output_schema) if output_schema is not None else None,
        )
        return self

    def _a2a_client(self) -> SecureAgentA2AClient:
        if self._a2a_client_config is None:
            raise SecureAgentConfigurationError("A2A client protocol is not configured")
        if self._a2a_client_integration is None:
            self._a2a_client_integration = SecureAgentA2AClient(self._a2a_client_config)
        return self._a2a_client_integration

    async def resolve_agent_card(self, agent_url: str) -> AgentCard:
        """Resolve and return the authoritative native Agent Card."""
        return await self._a2a_client().resolve_agent_card(agent_url)

    async def a2a_client(self, agent_url: str) -> Client:
        """Return a configured native ``a2a-sdk`` client."""
        return await self._a2a_client().connect(agent_url)

    async def discover(
        self,
        *,
        query: str | None = None,
        capability: str | None = None,
        category: str | None = None,
        provider_id: str | None = None,
        protocol: str | None = "A2A",
        role: str | None = "A2A_PROVIDER",
        tags: tuple[str, ...] = (),
        limit: int = 20,
    ) -> tuple[DiscoveredAgent, ...]:
        """Discover providers through Platform-owned Agent Nebula transport."""
        if self._nebula_config is None:
            raise SecureAgentConfigurationError("discover() requires nebula_config")
        if not 1 <= limit <= 100:
            raise SecureAgentConfigurationError("Discovery limit must be between 1 and 100")
        parameters: dict[str, Any] = {
            "limit": limit,
            "published_only": True,
            "sort_by": "relevance",
        }
        for name, value in (
            ("q", query),
            ("capability", capability),
            ("category", category),
            ("provider_id", provider_id),
            ("protocol", protocol),
            ("role", role),
        ):
            if value and value.strip():
                parameters[name] = value.strip()
        normalized_tags = tuple(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
        if normalized_tags:
            parameters["tag"] = normalized_tags[0]
        service = NebulaDiscoveryServiceFactory.create(self._nebula_config)
        try:
            return DiscoveryNormalizer().normalize(await service.search(parameters))
        finally:
            await service.close()

    def compose(self):
        """Compose the configured A2A server from the new Platform A2A boundary."""
        if self._a2a_server_config is None:
            raise SecureAgentConfigurationError("A2A server protocol is not configured")
        if not self._a2a_skills:
            raise SecureAgentConfigurationError("At least one A2A skill is required")
        self._application = SecureAgentA2AServer(
            configuration_file=self._a2a_server_config,
            skills=tuple(self._a2a_skills.values()),
            logging=self.logging,
        )
        return self._application

    def run(self) -> None:
        """Compose and run the configured A2A server."""
        self.compose().run()

    async def close(self) -> None:
        """Release client-side security resources."""
        if self._a2a_client_integration is not None:
            await self._a2a_client_integration.close()
            self._a2a_client_integration = None
