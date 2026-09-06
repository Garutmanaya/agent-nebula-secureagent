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

For A2A, the adapter performs only the narrow type adaptation from protocol-neutral `SkillDefinition` objects to Platform's A2A executable-skill contract. Agent Card parsing and validation, official A2A request handling, extension processing, skill dispatch, security enforcement, hosting, and lifecycle remain Platform responsibilities.

## A2A multi-skill dispatch

Official A2A `SendMessage` does not provide a first-class skill identifier. Agent Nebula Platform addresses deterministic multi-skill invocation through the Agent Nebula A2A skill-selection extension using official A2A extension and metadata facilities; official A2A models are not modified.

SecureAgent does not duplicate that extension. It passes every registered A2A business skill to Platform. Platform validates that each executable skill is published by the Agent Card and, for multi-skill providers, requires explicit client-side skill selection before dispatch. Single-skill providers remain compatible with ordinary A2A invocation because Platform can dispatch the only registered skill when the extension is not requested.
