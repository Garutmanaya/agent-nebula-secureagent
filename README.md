# Agent Nebula SecureAgent

`agent-nebula-secureagent` is the developer-facing API for building agents on Agent Nebula. It intentionally presents one protocol-neutral programming model: developers define business skills once, select the protocol roles their process needs, and let `agent-nebula-platform` compose the protocol, security, transport, lifecycle, and optional Agent Nebula integration.

SecureAgent is not a replacement implementation of A2A, MCP, REST, OAuth, DPoP, or Agent Nebula Registry APIs. It is the thin composition facade above `agent-nebula-platform`, which in turn depends on `agent-nebula-sdk` for standards/security primitives.

```text
Application code
      |
      v
agent-nebula-secureagent     developer API, skills, protocol selection
      |
      v
agent-nebula-platform        protocol plugins, security composition, lifecycle,
      |                      A2UI, health, Registry integration
      v
agent-nebula-sdk             OAuth/JWT/JWK/JOSE/DPoP and standards primitives
```

## Programming model

The public interface is deliberately not `SecureA2AAgent`, `SecureRestAgent`, or `SecureMcpAgent`. `SecureAgent` is the common abstraction. Protocols are selected independently:

```python
from agent_nebula_secureagent import ProtocolType, SecureAgent

agent = SecureAgent(
    "application.conf",
    nebula_config="nebula.conf",
)
agent.use_protocol(
    ProtocolType.A2A,
    role="server",
    config="a2aserver.conf",
)

@agent.skill("inventory.lookup", description="Look up current inventory")
async def inventory_lookup(payload):
    return {"sku": payload["sku"], "available": 12}

agent.run()
```

The skill contains business behavior only. A2A Agent Card parsing, official A2A request handling, OAuth protected-resource composition, DPoP validation, TLS, Agent Nebula registration, health, FastAPI/Uvicorn lifecycle, and shutdown are Platform responsibilities.

## Protocols

The API recognizes `a2a`, `rest`, and `mcp` through `ProtocolType`, so application code and extension contracts do not need protocol-specific SecureAgent classes.

| Protocol | SecureAgent server adapter | Platform capability | Notes |
|---|---|---|---|
| A2A 1.0 | Available | Available | Uses the official A2A SDK through Platform. |
| REST | Not yet exposed by this facade | Platform has REST/FastAPI skill transport | A dedicated SecureAgent REST configuration/composer should be added without changing the public skill model. |
| MCP | Not yet exposed | Not currently implemented by Platform | The common adapter contract reserves the boundary; SecureAgent does not claim MCP functionality that Platform does not provide. |

This distinction is intentional: the public API is protocol-neutral, while actual protocol availability is determined by registered Platform-backed adapters.

## Agent Nebula integration

Agent Nebula integration is optional and independent of A2A. Supplying `nebula.conf` enables Platform's Registry integration for a compatible server composition. For A2A, Platform derives the standard Agent Card URI, builds the registration payload, performs configured onboarding, persists registration state, and uses the configured Registry TLS/authentication policy. Without `nebula.conf`, the A2A server remains a standalone standards-based A2A server.

Agent Nebula adds enterprise discovery/registration and platform lifecycle integration; it does not replace the underlying A2A protocol or its endpoint security.

## Configuration ownership

Configuration is split by responsibility:

- `application.conf` — protocol-neutral application identity and filesystem roots.
- `a2aserver.conf` — A2A Agent Card, listener, TLS, interfaces, skills, and A2A security declaration.
- `a2aclient.conf` — outbound A2A transport, TLS, credentials, and optional discovered OAuth client identity.
- `nebula.conf` — optional Agent Nebula Registry endpoint, TLS, registration authentication, retry, and state behavior.
- REST/MCP — no SecureAgent-specific configuration format is invented until the corresponding Platform composition contract exists.

Every currently supported field is documented under [docs/configuration](docs/configuration/README.md).

## Package structure

```text
src/agent_nebula_secureagent/
├── secure_agent.py          # protocol-neutral public facade
├── exceptions.py            # stable facade exceptions
└── protocols/
    ├── base.py              # ProtocolType/Role and adapter contract
    ├── registry.py          # adapter registration and lookup
    └── a2a.py               # thin Platform A2A adapter
```

Business models (`SkillDefinition`, `SkillInvocation`, `SkillResult`) are owned by Platform and reused rather than duplicated.

## Plugin and adapter composition

SecureAgent does not maintain a second plugin framework. `ProtocolAdapterRegistry` selects a protocol adapter; the adapter translates facade intent into Platform inputs. Platform then composes its own `RuntimePlugin` implementations and lifecycle phases.

```text
SecureAgent
  -> ProtocolAdapterRegistry
      -> A2AServerProtocolAdapter
          -> A2AStandaloneApplicationComposer (Platform)
              -> RuntimeFeatureComponents
              -> Platform plugins
              -> AgentRuntime
```

This keeps protocol code out of the facade and prevents duplication of Platform's plugin lifecycle.

## Documentation

- [Architecture](docs/architecture.md)
- [Public API](docs/api/README.md)
- [Configuration reference](docs/configuration/README.md)
- [A2A](docs/a2a.md)
- [REST and MCP](docs/protocols.md)
- [Skills](docs/skills.md)
- [A2UI](docs/a2ui.md)
- [Agent Nebula integration](docs/nebula.md)
- [Security boundary](docs/security.md)
