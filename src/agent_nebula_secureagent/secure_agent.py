"""Protocol-neutral developer facade for Agent Nebula Platform."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import inspect
from pathlib import Path
from typing import Any, TypeVar, cast

from agent_nebula_platform.integrations.nebula import NebulaDiscoveryServiceFactory
from agent_nebula_platform.skills import (
    SkillDefinition,
    SkillHandler,
    SkillInvocation,
    SkillResult,
)

from .discovery import DiscoveredAgent, DiscoveryNormalizer
from .exceptions import SecureAgentConfigurationError, SecureAgentSkillRegistrationError
from .protocols import (
    A2AClientProtocolAdapter,
    A2AServerProtocolAdapter,
    ProtocolAdapterRegistry,
    ProtocolConfiguration,
    ProtocolRole,
    ProtocolType,
)

Handler = TypeVar("Handler", bound=Callable[..., Any])


class SecureAgent:
    """Small public API that delegates infrastructure to Agent Nebula Platform.

    SecureAgent owns developer intent: application configuration, selected
    protocols, business skills, and optional Agent Nebula integration. It does
    not implement A2A, OAuth, DPoP, Registry transport, FastAPI routing, or
    listener lifecycle; those responsibilities belong to Platform and SDK.

    Args:
        config: Generic SecureAgent configuration file. The filename is user-defined.
        nebula_config: Optional Agent Nebula Registry integration configuration.
        a2ui_config: Optional independent A2UI configuration file. SecureAgent
            stores the location only; Platform owns parsing and validation.
        protocol_registry: Optional adapter registry for extension/testing.
    """

    def __init__(
        self,
        config: str | Path = "secureagent.conf",
        *,
        nebula_config: str | Path | None = None,
        a2ui_config: str | Path | None = None,
        protocol_registry: ProtocolAdapterRegistry | None = None,
    ) -> None:
        self._application_config = Path(config)
        self._nebula_config = Path(nebula_config) if nebula_config is not None else None
        self._a2ui_config = Path(a2ui_config) if a2ui_config is not None else None
        self._protocols: dict[tuple[ProtocolType, ProtocolRole], ProtocolConfiguration] = {}
        self._skills: dict[str, SkillDefinition] = {}
        self._registry = protocol_registry or ProtocolAdapterRegistry(
            server_adapters=(A2AServerProtocolAdapter(),),
            client_adapters=(A2AClientProtocolAdapter(),),
        )
        self._application = None

    @property
    def skills(self) -> tuple[SkillDefinition, ...]:
        """Return registered business skills in registration order."""
        return tuple(self._skills.values())

    @property
    def protocols(self) -> tuple[ProtocolConfiguration, ...]:
        """Return configured protocol roles in configuration order."""
        return tuple(self._protocols.values())

    @property
    def application(self):
        """Return the composed Platform application after ``compose()``."""
        return self._application

    def use_protocol(
        self,
        protocol: ProtocolType | str,
        *,
        role: ProtocolRole | str = ProtocolRole.SERVER,
        config: str | Path,
    ) -> SecureAgent:
        """Enable one protocol role without exposing protocol implementation classes.

        Args:
            protocol: Protocol name or ``ProtocolType`` (`a2a`, `rest`, `mcp`).
            role: Direction of use (`server` or `client`).
            config: Protocol-specific configuration file path.

        Returns:
            This SecureAgent, enabling fluent configuration.

        Raises:
            SecureAgentConfigurationError: If the protocol/role is invalid or
                the same protocol role is configured twice.
        """
        try:
            protocol_type = ProtocolType(protocol)
            protocol_role = ProtocolRole(role)
        except ValueError as exc:
            raise SecureAgentConfigurationError(str(exc)) from exc
        key = (protocol_type, protocol_role)
        if key in self._protocols:
            raise SecureAgentConfigurationError(
                f"Protocol role already configured: {protocol_type.value}/{protocol_role.value}"
            )
        self._protocols[key] = ProtocolConfiguration(
            protocol=protocol_type,
            role=protocol_role,
            configuration_file=Path(config),
        )
        return self

    def skill(
        self,
        skill_id: str,
        *,
        description: str = "",
        scopes: tuple[str, ...] | None = None,
    ) -> Callable[[Handler], Handler]:
        """Register one transport-neutral business skill.

        Args:
            skill_id: Stable, non-empty capability identifier.
            description: Human-readable capability description.
            scopes: OAuth scopes required by transports that enforce OAuth. When
                omitted, the skill identifier is used as the secure default.

        Returns:
            Decorator that records the skill and returns the original function.

        Raises:
            SecureAgentSkillRegistrationError: On blank/duplicate identifiers,
                blank scopes, or a non-callable handler.
        """
        normalized_id = skill_id.strip()
        if not normalized_id:
            raise SecureAgentSkillRegistrationError("Skill identifier must not be blank")
        if normalized_id in self._skills:
            raise SecureAgentSkillRegistrationError(f"Skill is already registered: {normalized_id}")
        normalized_scopes = tuple(
            dict.fromkeys(scope.strip() for scope in (scopes or (normalized_id,)))
        )
        if not normalized_scopes or any(not scope for scope in normalized_scopes):
            raise SecureAgentSkillRegistrationError(
                f"Skill '{normalized_id}' must contain only non-blank scopes"
            )

        def register(handler: Handler) -> Handler:
            if not callable(handler):
                raise SecureAgentSkillRegistrationError(
                    f"Skill '{normalized_id}' handler must be callable"
                )

            async def platform_handler(invocation: SkillInvocation) -> SkillResult:
                result = cast(Callable[..., Any], handler)(invocation.payload)
                if inspect.isawaitable(result):
                    result = await result
                if isinstance(result, SkillResult):
                    return result
                if isinstance(result, Mapping):
                    return SkillResult(data=dict(result))
                raise SecureAgentSkillRegistrationError(
                    f"Skill '{normalized_id}' must return a mapping or SkillResult"
                )

            self._skills[normalized_id] = SkillDefinition(
                skill_id=normalized_id,
                handler=cast(SkillHandler, platform_handler),
                description=description.strip(),
                required_scopes=normalized_scopes,
            )
            return handler

        return register

    def _require_client_configuration(
        self, protocol: ProtocolType | str
    ) -> tuple[ProtocolType, ProtocolConfiguration]:
        """Resolve one configured client role or fail with facade-level context."""
        try:
            protocol_type = ProtocolType(protocol)
        except ValueError as exc:
            raise SecureAgentConfigurationError(str(exc)) from exc
        configuration = self._protocols.get((protocol_type, ProtocolRole.CLIENT))
        if configuration is None:
            raise SecureAgentConfigurationError(
                f"Client protocol is not configured: {protocol_type.value}"
            )
        return protocol_type, configuration

    async def resolve_agent_card(
        self,
        agent_url: str,
        *,
        protocol: ProtocolType | str = ProtocolType.A2A,
    ) -> dict[str, Any]:
        """Resolve a remote A2A Agent Card without exposing A2A wire models."""
        protocol_type, configuration = self._require_client_configuration(protocol)
        if protocol_type is not ProtocolType.A2A:
            raise SecureAgentConfigurationError(
                "resolve_agent_card() is available only for the A2A protocol"
            )
        adapter = self._registry.require_client(protocol_type)
        return dict(
            await adapter.resolve_remote(
                protocol_config=configuration.configuration_file,
                target=agent_url,
            )
        )

    async def send_message_to(
        self,
        agent_url: str,
        *,
        text: str | None = None,
        data: Mapping[str, Any] | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        skill_id: str | None = None,
        protocol: ProtocolType | str = ProtocolType.A2A,
    ) -> tuple[dict[str, Any], ...]:
        """Send through a configured client protocol using Platform-owned transport.

        ``skill_id`` is a facade convenience. For A2A, Platform validates it
        against the remote Agent Card and maps it to the Agent Nebula formal A2A
        skill-selection extension; SecureAgent never changes official A2A models.
        """
        protocol_type, configuration = self._require_client_configuration(protocol)
        adapter = self._registry.require_client(protocol_type)
        return await adapter.send_message(
            protocol_config=configuration.configuration_file,
            target=agent_url,
            text=text,
            data=data,
            context_id=context_id,
            task_id=task_id,
            skill_id=skill_id,
            resource=None,
            a2ui_config=self._a2ui_config,
        )

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
            raise SecureAgentConfigurationError(
                "discover() requires nebula_config on SecureAgent"
            )
        if not 1 <= limit <= 100:
            raise SecureAgentConfigurationError(
                "Discovery limit must be between 1 and 100"
            )
        parameters: dict[str, Any] = {
            "limit": limit, "published_only": True, "sort_by": "relevance"
        }
        for name, value in (("q", query), ("capability", capability), ("category", category), ("provider_id", provider_id), ("protocol", protocol), ("role", role)):
            if value and value.strip():
                parameters[name] = value.strip()
        normalized_tags = tuple(dict.fromkeys(tag.strip() for tag in tags if tag.strip()))
        if normalized_tags:
            parameters["tag"] = normalized_tags[0]
        service = NebulaDiscoveryServiceFactory.create(self._nebula_config)
        try:
            payload = await service.search(parameters)
            return DiscoveryNormalizer().normalize(payload)
        finally:
            await service.close()

    async def send_message(
        self,
        agent: DiscoveredAgent,
        *,
        text: str | None = None,
        data: Mapping[str, Any] | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        skill_id: str | None = None,
    ) -> tuple[dict[str, Any], ...]:
        """Invoke a discovered A2A provider using Registry resource metadata."""
        endpoint, resource = agent.require_a2a_invocation()
        protocol_type, configuration = self._require_client_configuration(ProtocolType.A2A)
        adapter = self._registry.require_client(protocol_type)
        return await adapter.send_message(
            protocol_config=configuration.configuration_file,
            target=endpoint,
            text=text,
            data=data,
            context_id=context_id,
            task_id=task_id,
            skill_id=skill_id,
            resource=resource,
            a2ui_config=self._a2ui_config,
        )

    async def close(self) -> None:
        """Close the composed server application when one exists."""
        if self._application is None:
            return
        close = getattr(self._application, "close", None)
        if close is not None:
            result = close()
            if inspect.isawaitable(result):
                await result
        self._application = None

    def compose(self):
        """Compose the configured server protocol into a Platform application.

        Returns:
            Protocol-specific application implementing ``run`` and ``close``.

        Raises:
            SecureAgentConfigurationError: If no server protocol or no skill is
                configured, or multiple server listeners are requested. Multi-
                listener process composition belongs to Platform, not this facade.
        """
        servers = tuple(
            item for item in self._protocols.values() if item.role is ProtocolRole.SERVER
        )
        if len(servers) != 1:
            raise SecureAgentConfigurationError(
                "SecureAgent currently requires exactly one configured server protocol"
            )
        if not self._skills:
            raise SecureAgentConfigurationError("At least one business skill is required")
        server = servers[0]
        adapter = self._registry.require_server(server.protocol)
        self._application = adapter.compose(
            application_config=self._application_config,
            protocol_config=server.configuration_file,
            nebula_config=self._nebula_config,
            skills=self.skills,
            a2ui_config=self._a2ui_config,
        )
        return self._application

    def run(self) -> None:
        """Compose, start, and block on the selected Platform-owned server."""
        self.compose().run()
