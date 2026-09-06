# Public API reference

## `SecureAgent`

### `SecureAgent(application_config="application.conf", *, nebula_config=None, protocol_registry=None)`

Creates the facade without starting infrastructure.

- `application_config: str | Path` — Platform `application.conf`. Default: `application.conf`.
- `nebula_config: str | Path | None` — optional Registry integration file. `None` means no Agent Nebula registration.
- `protocol_registry: ProtocolAdapterRegistry | None` — dependency-injection/extension point. Normal applications omit it.

### `use_protocol(protocol, *, role="server", config)`

Adds one protocol role and returns the same `SecureAgent` for fluent setup.

- `protocol: ProtocolType | str` — `a2a`, `rest`, or `mcp`.
- `role: ProtocolRole | str` — `server` or `client`.
- `config: str | Path` — protocol-owned configuration file.

Duplicate protocol/role pairs are rejected. Recognition of a protocol name does not imply an installed adapter; composition fails explicitly when Platform does not provide the requested capability.

### `skill(skill_id, *, description="", scopes=None, input_schema=None, output_schema=None)`

Decorator registering transport-neutral business behavior.

- `skill_id: str` — stable, nonblank capability identifier.
- `description: str` — human-readable description.
- `scopes: tuple[str, ...] | None` — required OAuth scopes. When omitted, `(skill_id,)` is used as the secure default.
- `input_schema: Mapping[str, Any] | None` — optional JSON Schema for input.
- `output_schema: Mapping[str, Any] | None` — optional JSON Schema for output.

A handler receives a plain mapping payload. It may be synchronous or asynchronous and may return either a mapping or Platform `SkillResult`. Mapping results are converted to `SkillResult(data=...)`.

### `compose()`

Validates the selected server protocol and skills, resolves the protocol adapter, and asks Platform to build the application. Returns the Platform-backed application. It does not start the listener.

The current facade requires exactly one server protocol per process. This avoids inventing listener/process orchestration outside Platform.

### `run()`

Calls `compose()` and then the Platform application's `run()`. The call blocks for standalone servers.

### `skills`

Read-only tuple of Platform `SkillDefinition` objects registered with the facade.

### `protocols`

Read-only tuple of `ProtocolConfiguration` objects.

### `application`

The composed application after `compose()`; otherwise `None`.

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

### `ProtocolAdapterRegistry(adapters=())`
Creates a registry from server adapters.

### `register(adapter)`
Registers one `ServerProtocolAdapter`; duplicate protocol ownership raises `SecureAgentProtocolError`.

### `require_server(protocol)`
Returns the registered server adapter or raises `SecureAgentProtocolError`.

## Exceptions

- `SecureAgentError` — base facade error.
- `SecureAgentConfigurationError` — invalid facade/protocol configuration.
- `SecureAgentSkillRegistrationError` — invalid or duplicate business skill.
- `SecureAgentProtocolError` — requested protocol adapter is unavailable or duplicated.
