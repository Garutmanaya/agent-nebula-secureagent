# Architecture

SecureAgent is a facade, not a runtime. Its stable responsibilities are: collect developer intent, register transport-neutral business skills, select protocol roles, and delegate composition to Platform.

## Dependency rule

`agent-nebula-secureagent -> agent-nebula-platform -> agent-nebula-sdk`.

The reverse dependency is forbidden. SecureAgent must not import low-level SDK OAuth/JOSE/JWT implementations directly and must not recreate Platform protocol plugins.

## Common protocol interface

`ProtocolType` names A2A, REST, and MCP. `ProtocolRole` names server/client direction. `ProtocolConfiguration` binds a protocol/role to its protocol-owned file. `ServerProtocolAdapter` is the extension contract. `ProtocolAdapterRegistry` resolves the implementation.

This is intentionally different from the historical Connect shape: there is one `SecureAgent`; no protocol-specific SecureAgent subclass or parallel A2A facade is required.

## Composition boundary

A server adapter receives only `config`, its protocol configuration, optional `nebula_config`, and immutable Platform `SkillDefinition` objects. It returns an application lifecycle object. Everything below that boundary belongs to Platform.

## Current A2A constraint

A2A 1.0 `SendMessage` does not provide a standard skill identifier. The current Platform A2A composer therefore accepts exactly one selected executable business skill. SecureAgent preserves this behavior and does not add proprietary wire metadata. Multi-skill A2A routing requires an explicit application/router design at the Platform layer.
