"""Protocol-neutral developer facade for Agent Nebula Platform."""
from __future__ import annotations

from collections.abc import Callable, Mapping
import inspect
from pathlib import Path
from typing import Any, TypeVar, cast

from agent_nebula_platform.skills import (
    SkillDefinition,
    SkillHandler,
    SkillInvocation,
    SkillResult,
)

from .exceptions import SecureAgentConfigurationError, SecureAgentSkillRegistrationError
from .protocols import (
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
        protocol_registry: Optional adapter registry for extension/testing.
    """

    def __init__(
        self,
        config: str | Path = "secureagent.conf",
        *,
        nebula_config: str | Path | None = None,
        protocol_registry: ProtocolAdapterRegistry | None = None,
    ) -> None:
        self._application_config = Path(config)
        self._nebula_config = Path(nebula_config) if nebula_config is not None else None
        self._protocols: dict[tuple[ProtocolType, ProtocolRole], ProtocolConfiguration] = {}
        self._skills: dict[str, SkillDefinition] = {}
        self._registry = protocol_registry or ProtocolAdapterRegistry(
            (A2AServerProtocolAdapter(),)
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
        )
        return self._application

    def run(self) -> None:
        """Compose, start, and block on the selected Platform-owned server."""
        self.compose().run()
