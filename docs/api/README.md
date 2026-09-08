# Public API reference

## `SecureAgent`

### `SecureAgent(config="secureagent.conf", *, nebula_config=None, a2ui_config=None, protocol_registry=None)`

Creates the facade without starting infrastructure.

- `config: str | Path` — Platform generic SecureAgent configuration. Default: `secureagent.conf`.
- `nebula_config: str | Path | None` — optional Registry integration file. `None` means no Agent Nebula registration.
- `a2ui_config: str | Path | None` — optional independent `a2ui.conf`. SecureAgent stores the path; Platform owns parsing, validation, negotiation, and protocol-specific binding.
- `protocol_registry: ProtocolAdapterRegistry | None` — dependency-injection/extension point. Normal applications omit it.

`a2ui_config` is independent of `config`, `a2aserver.conf`, and `a2aclient.conf`. Supplying it does not add A2UI fields to those files.

### `use_protocol(protocol, *, role="server", config)`

Adds one protocol role and returns the same `SecureAgent` for fluent setup.

- `protocol: ProtocolType | str` — `a2a`, `rest`, or `mcp`.
- `role: ProtocolRole | str` — `server` or `client`.
- `config: str | Path` — protocol-owned configuration file.

Duplicate protocol/role pairs are rejected. Recognition of a protocol name does not imply an installed adapter; composition fails explicitly when Platform does not provide the requested capability.

### `skill(skill_id, *, description="", scopes=None)`

Decorator registering transport-neutral business behavior.

- `skill_id: str` — stable, nonblank capability identifier.
- `description: str` — human-readable description.
- `scopes: tuple[str, ...] | None` — required OAuth scopes. When omitted, `(skill_id,)` is used as the secure default.

A handler receives a plain mapping payload. It may be synchronous or asynchronous and may return either a mapping or Platform `SkillResult`. Mapping results are converted to `SkillResult(data=...)`.

An explicit `SkillResult` is preserved intact:

```text
SkillResult
├── data       structured business result
├── metadata   result/application metadata
└── ui         optional A2UI surface
```

SecureAgent does not convert `ui` into an A2A DataPart. Platform's protocol adapter owns that mapping.

### `compose()`

Validates the selected server protocol and skills, resolves the protocol adapter, and asks Platform to build the application. Returns the Platform-backed application. It does not start the listener.

The current facade requires exactly one server protocol per process. This avoids inventing listener/process orchestration outside Platform.

When `a2ui_config` is supplied, the protocol adapter delegates loading to Platform and passes the resolved A2UI configuration into Platform composition. SecureAgent does not parse A2UI settings itself.

### `run()`

Calls `compose()` and then the Platform application's `run()`. The call blocks for standalone servers.

### `skills`

Read-only tuple of Platform `SkillDefinition` objects registered with the facade.

### `protocols`

Read-only tuple of `ProtocolConfiguration` objects.

### `application`

The composed application after `compose()`; otherwise `None`.

## A2A client operations

When an A2A client role is configured, SecureAgent delegates Agent Card resolution and message sending to Platform. If `a2ui_config` is supplied, the same independent A2UI configuration is passed to Platform's A2A client service so Platform can perform A2UI negotiation when supported by the remote Agent Card.

SecureAgent does not expose `AgentExtension`, `ClientCallContext`, extension service parameters, A2UI MIME handling, or renderer-capability metadata as public facade concepts.

## Protocol types

### `ProtocolType`

- `ProtocolType.A2A` (`"a2a"`)
- `ProtocolType.REST` (`"rest"`)
- `ProtocolType.MCP` (`"mcp"`)

### `ProtocolRole`

- `ProtocolRole.SERVER` (`"server"`)
- `ProtocolRole.CLIENT` (`"client"`)

### `ProtocolConfiguration(protocol, role, configuration_file)`

Immutable value object containing the selected `ProtocolType`, `ProtocolRole`, and configuration `Path`.

## `ProtocolAdapterRegistry`

### `ProtocolAdapterRegistry(server_adapters=(), client_adapters=())`
Creates a role-aware registry from server and client adapters.

### `register_server(adapter)` / `register_client(adapter)`
Registers one role-specific protocol adapter; duplicate ownership for the same role raises `SecureAgentProtocolError`. `register(adapter)` remains a server-registration compatibility alias.

### `require_server(protocol)` / `require_client(protocol)`
Returns the registered role-specific adapter or raises `SecureAgentProtocolError`.

## Exceptions

- `SecureAgentError` — base facade error.
- `SecureAgentConfigurationError` — invalid facade/protocol configuration.
- `SecureAgentSkillRegistrationError` — invalid or duplicate business skill.
- `SecureAgentProtocolError` — requested protocol adapter is unavailable or duplicated.
