# A2A

SecureAgent's A2A adapter is intentionally thin. It adapts registered protocol-neutral `SkillDefinition` objects to Platform's executable-skill contract and delegates A2A composition to Agent Nebula Platform.

Platform loads the official A2A Agent Card, validates executable skills against published `AgentSkill.id` values, creates the official request-handler/task-store/executor bridge, composes protected-resource validation when required, configures the listener, and optionally enables Agent Nebula onboarding.

SecureAgent does not parse Agent Cards, implement A2A extensions, select OAuth schemes, validate access tokens/DPoP proofs, implement JSON-RPC/HTTP+JSON/gRPC bindings, or add fields to official A2A models. Those responsibilities remain in Platform and the official A2A SDK.

## Multiple skills

A SecureAgent A2A server may register one or more business skills with `@agent.skill(...)`. SecureAgent passes all registered skills to Platform without selecting or routing between them.

For a multi-skill provider, Platform advertises the Agent Nebula A2A skill-selection extension as required and deterministically dispatches the client-selected, advertised `AgentSkill.id`. For a single-skill provider, Platform advertises the same extension as optional so ordinary A2A clients remain compatible.

Every executable SecureAgent skill must have a corresponding `agent_card.skills[].id` in `a2aserver.conf`. Platform owns this validation and fails composition when the executable and published skill sets are inconsistent.

Skill-specific security requirements also remain a Platform concern. A Nebula-aware client can select a skill before invocation so Platform can resolve the corresponding security requirements and acquire least-privilege authorization. The provider validates authorization before the selected business handler is reached.

## A2UI extension coexistence

When A2UI is enabled through the independent `a2ui.conf`, Platform may advertise and negotiate the A2UI v1.0 extension in addition to the skill-selection extension. The two extensions are independent and composable on the same A2A invocation.

A `SkillResult` may therefore produce multiple response parts:

```text
A2A Message
├── optional TextPart projection
├── DataPart: structured business result
└── DataPart: ordered A2UI messages
              metadata.mimeType = application/a2ui+json
```

A2UI configuration, extension negotiation, renderer capability metadata, and A2UI DataPart conversion remain Platform responsibilities. They are not encoded in `a2aserver.conf` and are not implemented by SecureAgent.

## Client invocation

SecureAgent exposes Platform's A2A client through the same `use_protocol()` model:

```python
agent.use_protocol("a2a", role="client", config="a2aclient.conf")

card = await agent.resolve_agent_card("https://provider.example")
responses = await agent.send_message_to(
    "https://provider.example",
    data={"sku": "ABC"},
    skill_id="inventory.lookup",
)
```

`resolve_agent_card()` returns a plain dictionary so applications do not depend on A2A protobuf types. `send_message_to()` delegates request construction, Agent Card validation, transport selection, TLS/security negotiation, extension composition, and client cleanup to Platform.

When `skill_id` is supplied, Platform validates it against the remote Agent Card and activates the Agent Nebula skill-selection extension using the official A2A extension mechanism. When A2UI is independently enabled and supported by the remote Agent Card, Platform also contributes A2UI negotiation. SecureAgent does not construct or modify A2A wire models.

A SecureAgent may configure both `role="server"` and `role="client"` for A2A. The server is composed by `compose()`/`run()` while outbound operations use the independently configured client adapter.

## Agent Nebula discovery and secured invocation

When `nebula_config` and an A2A client protocol are configured, `SecureAgent.discover()` delegates Registry access, TLS, and Registry authentication to Platform. The returned `DiscoveredAgent` keeps the Registry protected-resource identifier separate from the A2A endpoint. `SecureAgent.send_message()` passes both values to Platform so OAuth uses the authoritative Registry resource while the official A2A client uses the advertised endpoint. Static HTTP credentials, API keys, mTLS, OIDC, OAuth2, RFC 7591 dynamic registration, private-key JWT client authentication, and DPoP remain Platform/SDK responsibilities selected from the remote Agent Card.
