# Security and authorization

SecureAgent offers a small developer-facing API; **Platform enforces protocol security**, and `agent-nebula-sdk` supplies standards and cryptographic primitives. SecureAgent does not implement its own OAuth server or replace the official A2A security model.

## Responsibilities

| Layer | Responsibility |
|---|---|
| SecureAgent | Skill identifiers, optional scope requirements, protocol selection, configuration references |
| Platform | Agent Card security interpretation, protected-resource integration, transport authentication, authorization checks, lifecycle |
| Security SDK | OAuth, JWT/JWK/JOSE, DPoP and supporting standards primitives |
| Hosted Agent Nebula (optional) | OAuth services, Registry identity/discovery, centrally managed policies and accounts |

## Authentication mechanisms

The Platform and security SDK support configurable security mechanisms, including OAuth 2.0 bearer-token validation, JWT validation, DPoP, and TLS/mTLS where applicable. Actual support for a given agent depends on its A2A security declaration, the selected protocol binding, and its runtime configuration. See [A2A server](configuration/a2aserver.md) and [A2A client](configuration/a2aclient.md) for the configuration contract.

**mTLS:** a trusted CA file is not proof of client-certificate authentication. The listener and client must be explicitly configured for mutual TLS. An ordinary HTTPS tunnel terminating TLS at a third-party edge does not pass through the original client TLS handshake.

## Skill scopes and policy-controlled invocation

For a skill registered with `@agent.skill(...)`, the default required OAuth scope is the skill identifier unless explicitly overridden. This is a default requirement, **not** a substitute for issuing appropriately scoped tokens or configuring enforcement. When hosted Agent Nebula policies are used, policy decisions are a separate authorization concern from A2A protocol handling.

```text
A2A client → authenticated request → Platform security checks
                                    → skill scope / applicable policy
                                    → skill handler (only if authorized)
```

An effective integration test must verify both an authorized invocation and rejection of a request lacking the required authorization. The [Agent Nebula integration guide](nebula.md) explains how hosted services fit into this flow; the [examples repository](https://github.com/garutmanaya/agent-nebula-secureagent-examples) contains runnable scenarios.

Keep credentials, private keys, and tokens out of Agent Cards, public documentation, and version control. Agent Card security declarations describe requirements; they are not credential storage.
