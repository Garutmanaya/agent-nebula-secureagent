# Getting started with SecureAgent

SecureAgent is the developer-facing API for Agent Nebula agents. An application defines business behavior in Python and expresses protocol, security, Agent Card, skill publication, and presentation capabilities through configuration and declarative artifacts.

The intended boundary is:

```text
Application business logic
        |
        v
agent-nebula-secureagent        public developer API
        |
        v
agent-nebula-platform           A2A/A2UI composition, lifecycle, security integration
        |
        +---- official a2a-sdk
        |
        v
agent-nebula-sdk                OAuth/JWT/DPoP/mTLS/PKI primitives
```

Application code should not import Platform or SDK APIs directly. SecureAgent is the supported application boundary.

## Project shape

A SecureAgent project should keep executable business behavior separate from configuration and presentation:

```text
my-agent/
├── agent.py
├── config/
│   ├── secureagent.conf
│   ├── a2aserver.conf
│   ├── a2aclient.conf          # only when the process acts as an A2A client
│   ├── a2ui.conf               # only when A2UI is enabled
│   └── nebula.conf             # only when Agent Nebula integration is enabled
└── skills/
    └── inventory.lookup/
        └── presentation.json   # only when the skill provides A2UI
```

`agent.py` contains business handlers and small SecureAgent API calls. It should not contain A2A envelopes, A2UI component trees, catalog negotiation, OAuth implementation, Agent Card construction, or Platform composition code.

## Configuration-driven agent definition

SecureAgent deliberately keeps most infrastructure and externally visible capability information out of Python:

- `secureagent.conf` owns generic runtime/application settings.
- `a2aserver.conf` owns the A2A listener, Agent Card, published skill definitions, interfaces, capabilities, and A2A security declarations.
- `a2aclient.conf` owns outbound A2A transport and security preferences.
- `a2ui.conf` owns A2UI version and catalog capabilities.
- `nebula.conf` owns optional Agent Nebula Registry integration.
- `presentation.json` owns a skill's declarative A2UI component topology and initial data model.

The Python `@agent.skill(...)` decorator binds executable business behavior to a stable skill identifier and, when needed, supplies machine-readable schema-contract metadata. For an A2A server, that identifier must match the corresponding skill published in `a2aserver.conf`. This keeps the Agent Card authoritative while keeping executable business logic explicit in Python.

## Minimal A2A agent

```python
from agent_nebula_secureagent import SecureAgent

agent = SecureAgent(config="config/secureagent.conf")
agent.use_protocol("a2a", role="server", config="config/a2aserver.conf")

@agent.skill("inventory.lookup", description="Look up inventory")
async def inventory_lookup(payload):
    return {"sku": payload["sku"], "available": 12}

agent.run()
```

The handler contains the business operation only. Platform owns official A2A request handling, Agent Card processing, transport binding, security enforcement, lifecycle, and response mapping.

## Add declarative A2UI

Enable A2UI by supplying its independent configuration:

```python
agent = SecureAgent(
    config="config/secureagent.conf",
    a2ui_config="config/a2ui.conf",
)
```

Load the skill-owned presentation once and create/update surfaces through SecureAgent:

```python
presentation = agent.load_a2ui_presentation(
    "skills/inventory.lookup/presentation.json"
)

@agent.skill("inventory.lookup", description="Look up inventory")
async def inventory_lookup(payload):
    result = {"sku": payload["sku"], "available": 12}
    surface = agent.create_a2ui_surface(
        presentation,
        data_model={"result": result},
    )
    return SkillResult(data=result, ui=surface)
```

The component tree belongs in `presentation.json`, not in this handler. Subsequent interaction should normally update the surface data model with `update_a2ui_surface()` rather than reconstructing the UI in Python.

An agent that does not need A2UI simply omits `a2ui.conf`, presentation files, and A2UI API calls.

## Security

A2A security declarations are configuration. SecureAgent/Platform translate those declarations into runtime security composition and use Agent Nebula SDK for the underlying OAuth, JWT, DPoP, mTLS, JOSE, and related standards primitives. Application handlers should not implement these mechanisms themselves.

See [security.md](security.md), [a2ui.md](a2ui.md), and the complete [configuration reference](configuration/README.md).
