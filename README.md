# Agent Nebula SecureAgent

**Build standards-based A2A agents with business skills in Python and protocol, security, and presentation defined through configuration.**

[Getting started](docs/getting-started.md) · [Configuration](docs/configuration/README.md) · [Architecture](docs/architecture.md) · [Security](docs/security.md) · [A2UI](docs/a2ui.md) · [Agent Nebula](docs/nebula.md) · [Examples](https://github.com/garutmanaya/agent-nebula-secureagent-examples)

`agent-nebula-secureagent` is the lightweight developer-facing facade over `agent-nebula-platform`. It uses the **official A2A Python SDK** through Platform rather than reimplementing A2A. A2UI is optional. An agent can run standalone without registering with Agent Nebula.

## Why SecureAgent?

Working directly with an A2A server requires assembling protocol handlers, Agent Card metadata, transport hosting, security integration, and lifecycle behavior around application logic. SecureAgent delegates those infrastructure responsibilities to Platform. Developers concentrate on skills while configuring published capabilities and security separately. This reduces duplicated infrastructure code; it does not remove the need to design and test business logic or access policies.

| Capability | What developers gain |
|---|---|
| **A2A 1.0** | Official SDK-based messaging, skills, tasks, streaming, and supported bindings via Platform |
| **One skill API** | Bind Python handlers to published skill identifiers; avoid protocol-specific business implementations |
| **Configuration-driven design** | Change Agent Cards, endpoints, TLS, OAuth, and Registry settings without rewriting skill handlers |
| **A2UI v1.0** | Return interactive UI surfaces with declarative `presentation.json` and configured catalogs |
| **Security integration** | Reuse Platform enforcement and SDK primitives for OAuth, scopes, TLS/mTLS, JWT, and DPoP where configured |
| **Optional Agent Nebula** | Register and discover agents; use hosted OAuth and policy services for controlled invocation |

## Architecture

```text
Business skills (Python) + configuration + optional A2UI presentation
                            |
                            v
                 agent-nebula-secureagent
                 (public application facade)
                            |
                            v
                  agent-nebula-platform
            (A2A/A2UI composition, security, lifecycle)
                   /                   \
          official a2a-sdk       agent-nebula-sdk
                                (security primitives)
                            |
                optional Agent Nebula services
            (Registry, discovery, OAuth, policy)
```

See [architecture and component boundaries](docs/architecture.md). A2A is implemented through the official SDK; REST and MCP are **not currently exposed as working SecureAgent server adapters** ([details](docs/protocols.md)).

## Quick start

Requires **Python 3.12**. Install the released package and its declared dependencies:

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install agent-nebula-secureagent==1.1.1
```

An A2A server defines its published skills in `a2aserver.conf` and binds executable handlers to those identifiers:

```python
from agent_nebula_secureagent import SecureAgent

agent = SecureAgent(config="config/secureagent.conf")
agent.use_protocol("a2a", role="server", config="config/a2aserver.conf")

@agent.skill("inventory.lookup", description="Look up inventory")
async def inventory_lookup(payload):
    return {"sku": payload["sku"], "available": 12}

agent.run()
```

This snippet illustrates the API; it requires valid configuration files. Follow the [complete getting-started guide](docs/getting-started.md) and the [runnable examples](https://github.com/garutmanaya/agent-nebula-secureagent-examples) for complete configurations and server/client commands.

## Configuration-driven development

| File | Responsibility |
|---|---|
| `secureagent.conf` | Application identity and generic runtime settings |
| `a2aserver.conf` | Agent Card, advertised skills, A2A bindings, listener and server security |
| `a2aclient.conf` | Outbound A2A connections, trust and client authentication |
| `a2ui.conf` | Optional A2UI capability and component catalogs |
| `presentation.json` | Optional skill-owned UI component tree, bindings, and actions |
| `nebula.conf` | Optional Agent Nebula Registry onboarding and registration |

The configuration formats, supported keys, and ownership boundaries are documented in the [configuration reference](docs/configuration/README.md). A2UI presentation remains separate from Python business logic ([A2UI guide](docs/a2ui.md)).

## Authentication and authorization

SecureAgent does **not** implement a competing authentication stack. Platform interprets A2A security declarations and composes enforcement; `agent-nebula-sdk` supplies reusable security primitives. Configuration determines which mechanisms are enabled. A trust bundle alone does not enable mTLS, and declaring an OAuth scope does not by itself establish a hosted policy decision. See [security and authorization](docs/security.md).

## Agent Nebula Enterprise Registry Hub (optional)

[Agent Nebula](https://agentnebula.ai) provides hosted A2A Registry and discovery, Explorer, Playground, OAuth, policy, and account-management services. Its organizational model is **Publisher → Provider → Agents**. Developers can register publicly reachable agents and test OAuth-scoped, policy-controlled invocation; local standalone examples do not require these services.

Start with [Agent Nebula integration](docs/nebula.md), then follow the [platform-integrated examples](https://github.com/garutmanaya/agent-nebula-secureagent-examples/tree/main/examples-nebula) for onboarding, registration, and invocation scenarios.

## Documentation

- [Getting started](docs/getting-started.md) · [Public API](docs/api/README.md) · [Skills](docs/skills.md)
- [Architecture](docs/architecture.md) · [A2A](docs/a2a.md) · [A2UI](docs/a2ui.md)
- [Configuration reference](docs/configuration/README.md) · [Security](docs/security.md)
- [Agent Nebula services and integration](docs/nebula.md) · [REST/MCP status](docs/protocols.md)
- [A2A Schema Contract extension](docs/agent-nebula-a2a-schema-contract-extension.md)

## License

Licensed under the [Apache License, Version 2.0](LICENSE). See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.
