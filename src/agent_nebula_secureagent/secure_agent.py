"""Protocol-neutral developer facade for Agent Nebula Platform."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import inspect
from pathlib import Path
from typing import Any, TypeVar, cast
from uuid import uuid4

from agent_nebula_platform.a2ui import A2UIComposer, A2UIConfiguration, A2UIPresentation, A2UISurface
from agent_nebula_platform.integrations.nebula import NebulaDiscoveryServiceFactory
from agent_nebula_platform.skills import (
    SkillDefinition,
    SkillHandler,
    SkillInvocation,
    SkillResult,
)

from .discovery import DiscoveredAgent, DiscoveryNormalizer
from .exceptions import SecureAgentConfigurationError, SecureAgentSkillRegistrationError
from .logging import SecureAgentLoggingConfiguration, load_logging_configuration
from .protocols import (
    A2AClientProtocolAdapter,
    A2AServerProtocolAdapter,
    ProtocolAdapterRegistry,
    ProtocolConfiguration,
    ProtocolRole,
    ProtocolType,
)

Handler = TypeVar("Handler", bound=Callable[..., Any])
A2UIActionHandler = Callable[..., Any]


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
        self._a2ui_action_handler: A2UIActionHandler | None = None
        self._a2ui_composer: A2UIComposer | None = None
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

    @property
    def logging(self) -> SecureAgentLoggingConfiguration:
        """Return validated console logging settings from ``secureagent.conf``."""

        return load_logging_configuration(self._application_config)

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
        schema_contract_id: str | None = None,
        input_schema: Mapping[str, Any] | None = None,
        output_schema: Mapping[str, Any] | None = None,
    ) -> Callable[[Handler], Handler]:
        """Register one transport-neutral business skill.

        Args:
            skill_id: Stable, non-empty capability identifier.
            description: Human-readable capability description.
            scopes: OAuth scopes required by transports that enforce OAuth. When
                omitted, the skill identifier is used as the secure default.
            schema_contract_id: Absolute immutable structured-contract identifier.
            input_schema: Optional JSON Schema for structured skill input.
            output_schema: Optional JSON Schema for structured skill output.

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
        normalized_contract_id = (schema_contract_id or "").strip() or None
        if (input_schema is not None or output_schema is not None) and normalized_contract_id is None:
            raise SecureAgentSkillRegistrationError(
                f"Skill '{normalized_id}' requires schema_contract_id when a schema is declared"
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
                schema_contract_id=normalized_contract_id,
                input_schema=dict(input_schema) if input_schema is not None else None,
                output_schema=dict(output_schema) if output_schema is not None else None,
            )
            return handler

        return register

    def _require_a2ui_composer(self) -> A2UIComposer:
        """Return the configuration-backed Platform composer for provider presentations."""
        if self._a2ui_config is None:
            raise SecureAgentConfigurationError(
                "A2UI presentation requires a2ui_config on SecureAgent"
            )
        if self._a2ui_composer is None:
            self._a2ui_composer = A2UIComposer(A2UIConfiguration.load(self._a2ui_config))
        return self._a2ui_composer

    def load_a2ui_presentation(self, path: str | Path) -> A2UIPresentation:
        """Load one skill-owned declarative presentation through Platform."""
        self._require_a2ui_composer()
        return A2UIPresentation.load(Path(path))

    def create_a2ui_surface(
        self,
        presentation: A2UIPresentation,
        *,
        surface_id: str | None = None,
        data_model: Mapping[str, Any] | None = None,
    ) -> A2UISurface:
        """Create a configured A2UI surface without exposing Platform to application code."""
        resolved_surface_id = surface_id or f"a2ui_{uuid4().hex}"
        return self._require_a2ui_composer().surface_from_presentation(
            surface_id=resolved_surface_id,
            presentation=presentation,
            data_model=dict(data_model) if data_model is not None else None,
        )

    def update_a2ui_surface(
        self,
        surface_id: str,
        *,
        data_model: Mapping[str, Any],
        path: str = "/",
    ) -> A2UISurface:
        """Update one existing A2UI surface using the configured Platform composer."""
        return self._require_a2ui_composer().update(
            surface_id=surface_id,
            data_model=dict(data_model),
            path=path,
        )

    def set_a2ui_action_handler(self, handler: A2UIActionHandler) -> SecureAgent:
        """Set the application callback for A2UI renderer-to-agent actions.

        The callback is server-side application behavior. SecureAgent only carries
        it across the composition boundary; Platform parses and dispatches the
        standards-defined A2UI action message.
        """
        if not callable(handler):
            raise SecureAgentConfigurationError("A2UI action handler must be callable")
        self._a2ui_action_handler = handler
        return self

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
    ):
        """Resolve and return the official ``a2a.types.AgentCard``.

        This method performs only configuration-driven resolution.  SecureAgent
        deliberately returns the native SDK model instead of maintaining a second
        AgentCard representation.
        """
        protocol_type, configuration = self._require_client_configuration(protocol)
        if protocol_type is not ProtocolType.A2A:
            raise SecureAgentConfigurationError(
                "resolve_agent_card() is available only for the A2A protocol"
            )
        adapter = self._registry.require_client(protocol_type)
        return await adapter.resolve_remote(
            protocol_config=configuration.configuration_file,
            target=agent_url,
        )

    async def a2a_client(self, agent_url: str):
        """Return a configured native ``a2a.client.Client``.

        AGENT NEBULA INTEGRATION:
        SecureAgent contributes only external configuration. Platform composes
        TLS and Agent Nebula security interceptors using official ``a2a-sdk``
        extension points, then returns the SDK client unchanged. Standard A2A
        operations must be invoked directly on that client.

        The caller owns ``Client.close()``. ``SecureAgent.close()`` releases the
        associated Platform credential-provider resources.
        """
        protocol_type, configuration = self._require_client_configuration(
            ProtocolType.A2A
        )
        adapter = self._registry.require_client(protocol_type)
        return await adapter.connect(
            protocol_config=configuration.configuration_file,
            target=agent_url,
        )

    async def send_message_to(
        self,
        agent_url: str,
        *,
        text: str | None = None,
        data: Mapping[str, Any] | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
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
            a2ui_config=self._a2ui_config,
        )

    async def send_a2ui_action(
        self,
        agent_url: str,
        *,
        name: str,
        surface_id: str,
        source_component_id: str,
        context: Mapping[str, Any] | None = None,
        data_model: Mapping[str, Any] | None = None,
        want_response: bool = False,
        action_id: str | None = None,
        context_id: str | None = None,
        task_id: str | None = None,
        protocol: ProtocolType | str = ProtocolType.A2A,
    ) -> tuple[dict[str, Any], ...]:
        """Send one A2UI renderer action without exposing A2A wire details."""
        if self._a2ui_config is None:
            raise SecureAgentConfigurationError(
                "send_a2ui_action() requires a2ui_config on SecureAgent"
            )
        protocol_type, configuration = self._require_client_configuration(protocol)
        adapter = self._registry.require_client(protocol_type)
        return await adapter.send_a2ui_action(
            protocol_config=configuration.configuration_file,
            target=agent_url,
            name=name,
            surface_id=surface_id,
            source_component_id=source_component_id,
            context=context,
            data_model=data_model,
            want_response=want_response,
            action_id=action_id,
            context_id=context_id,
            task_id=task_id,
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
        """Invoke a discovered A2A provider using its authoritative Agent Card security."""
        agent_card_location = agent.require_agent_card_location()
        protocol_type, configuration = self._require_client_configuration(ProtocolType.A2A)
        adapter = self._registry.require_client(protocol_type)
        return await adapter.send_message(
            protocol_config=configuration.configuration_file,
            target=agent_card_location,
            text=text,
            data=data,
            context_id=context_id,
            task_id=task_id,
            skill_id=skill_id,
            a2ui_config=self._a2ui_config,
        )

    async def close(self) -> None:
        """Release client integration resources and the composed server application."""
        for adapter in self._registry.client_adapters:
            close = getattr(adapter, "close", None)
            if close is not None:
                result = close()
                if inspect.isawaitable(result):
                    await result

        if self._application is not None:
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
            a2ui_action_handler=self._a2ui_action_handler,
            a2ui_config=self._a2ui_config,
        )
        return self._application

    def run(self) -> None:
        """Compose, start, and block on the selected Platform-owned server."""
        self.compose().run()
