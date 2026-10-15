# Architecture

SecureAgent is a facade, not a runtime. Its stable responsibilities are to collect developer intent, register transport-neutral business skills, select protocol roles, and delegate composition to Platform.

## Why the facade accelerates development

SecureAgent keeps skill handlers independent of A2A protocol envelopes, HTTP hosting, Agent Card parsing, and security implementation. Infrastructure is configured and composed by Platform, so a developer can reuse one business handler while changing supported bindings, published metadata, or optional A2UI presentation. This is an architectural reduction in boilerplate, not a measured performance claim.

## Dependency rule

`agent-nebula-secureagent -> agent-nebula-platform -> agent-nebula-sdk`.

The reverse dependency is forbidden. SecureAgent must not import low-level SDK OAuth/JOSE/JWT implementations directly and must not recreate Platform protocol plugins.

## Configuration ownership

Configuration is split by capability rather than accumulated in one application or protocol file:

```text
secureagent.conf   generic runtime/application settings
a2aserver.conf     A2A server and Agent Card
a2aclient.conf     A2A client
a2ui.conf          A2UI protocol capability
nebula.conf         optional Registry integration
```

A2UI is deliberately independent of A2A configuration. SecureAgent carries the optional `a2ui_config` reference across the facade boundary; Platform owns loading and validation.


## Application contract

Application code uses `agent-nebula-secureagent` as its Agent Nebula API boundary. It must not depend directly on Platform protocol/composition APIs or SDK security primitives. The intended application split is:

```text
Python (`agent.py`)              Configuration / declarative artifacts
-----------------------------   ---------------------------------------
business calculations           runtime/application settings
skill handlers                  Agent Card and published skills
SecureAgent facade calls        A2A interfaces and security declarations
                                A2UI capabilities/catalogs
                                A2UI `presentation.json` component trees
                                Agent Nebula Registry integration
```

For A2UI-enabled skills, Python owns dynamic business data while `presentation.json` owns presentation topology, bindings, actions, and catalog selection. Application code must not construct raw A2UI protocol envelopes or hardcode reusable component trees in Python.

For A2A, published skill definitions are configuration-driven through `a2aserver.conf`; executable handlers bind to the same stable identifier with `@agent.skill(...)`. Schema-contract metadata remains attached to the executable skill declaration where required. Platform validates the relationship between executable and published skills.

## Common protocol interface

`ProtocolType` names A2A, REST, and MCP. `ProtocolRole` names server/client direction. `ProtocolConfiguration` binds a protocol/role to its protocol-owned file. `ServerProtocolAdapter` and `ClientProtocolAdapter` are extension contracts. `ProtocolAdapterRegistry` resolves the implementation.

There is one `SecureAgent`; no protocol-specific SecureAgent subclass or parallel A2A facade is required.

## Composition boundary

A server adapter receives generic SecureAgent configuration, its protocol configuration, optional Nebula configuration, optional independent A2UI configuration, and immutable Platform `SkillDefinition` objects. It returns an application lifecycle object. Everything below that boundary belongs to Platform.

For A2A, the adapter performs only narrow adaptation from protocol-neutral `SkillDefinition` objects to Platform's executable-skill contract. It preserves the complete Platform `SkillResult`. Agent Card parsing and validation, official A2A request handling, extension processing, result mapping, security enforcement, hosting, and lifecycle remain Platform responsibilities.

## A2UI boundary

A2UI protocol/domain behavior belongs to `agent-nebula-platform.a2ui`. A2UI-over-A2A binding behavior belongs to Platform's A2A extension adapter. SecureAgent exposes only the independent configuration reference and `SkillResult` contract; it does not expose A2A extension objects, service parameters, DataParts, MIME handling, or renderer capability metadata.

This separation allows A2UI protocol versions and A2A binding details to evolve without changing business skill code or unrelated security/runtime functionality.

## A2A multi-skill dispatch

Official A2A `SendMessage` does not provide a first-class skill identifier. Agent Nebula Platform addresses deterministic multi-skill invocation through the Agent Nebula A2A skill-selection extension using official A2A extension and metadata facilities; official A2A models are not modified.

SecureAgent does not duplicate that extension. It passes every registered A2A business skill to Platform. Platform validates that each executable skill is published by the Agent Card and, for multi-skill providers, requires explicit client-side skill selection before dispatch. Single-skill providers remain compatible with ordinary A2A invocation because Platform can dispatch the only registered skill when the extension is not requested.
