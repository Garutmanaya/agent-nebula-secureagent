# A2UI

SecureAgent exposes A2UI as an optional presentation capability while Agent Nebula Platform owns the A2UI protocol implementation. A2UI is not a separate SecureAgent transport and does not introduce a separate endpoint or security path.

The current implementation targets A2UI `v1.0`. A2UI v1.0 is still evolving; Agent Nebula keeps version-specific models, validation, surfaces, actions, sessions, and capability negotiation in Platform so those details can evolve without moving protocol logic into application skills.

This keeps UI changes (component layout, binding and catalogs) in declarative files while Python handlers produce data. A2UI is optional and does not create a separate authentication path; it is carried through the supported A2A integration.

## Required application design

A SecureAgent application must keep **presentation definition separate from business logic**.

```text
agent.py
    business logic
    skill handlers
    SecureAgent API calls
          |
          +---- load/create/update presentation
          v
skills/<skill>/presentation.json
    component topology
    bindings
    initial data model
    actions
    component catalog selection
          |
          v
a2ui.conf
    A2UI version
    supported catalogs
    default catalog
    inline-catalog policy
```

A2UI component trees must not be hardcoded as Python dictionaries/lists in `agent.py`. The presentation belongs in `presentation.json`. Python computes business results and supplies dynamic data; SecureAgent/Platform create the protocol messages and update the surface.

This separation is intentional. Changing a layout, component, binding, or catalog selection should normally be a presentation/configuration change, not a business-code change.

## Declarative presentation

Load presentation JSON through the SecureAgent facade:

```python
presentation = agent.load_a2ui_presentation(
    "skills/inventory.lookup/presentation.json"
)
```

Create the initial surface with business data:

```python
surface = agent.create_a2ui_surface(
    presentation,
    data_model={"result": result},
)
```

For an existing interactive surface, update data rather than rebuilding the component topology in Python:

```python
surface = agent.update_a2ui_surface(
    surface_id,
    data_model={"result": updated_result},
)
```

`A2UIPresentation`/`A2UIComposer` are Platform implementation types. Application code accesses presentation behavior only through the SecureAgent methods above.

## Configuration boundary

A2UI configuration is independent from A2A configuration:

```text
secureagent.conf   -> generic SecureAgent runtime/application settings
a2aserver.conf     -> A2A server and Agent Card
a2aclient.conf     -> A2A client transport/security preferences
a2ui.conf          -> A2UI protocol and catalog capabilities
nebula.conf        -> optional Agent Nebula Registry integration
```

Applications opt in by passing the independent configuration file to the facade:

```python
agent = SecureAgent(
    config="secureagent.conf",
    a2ui_config="a2ui.conf",
)
```

SecureAgent stores the path and delegates parsing and validation to Platform's `A2UIConfiguration`. A2UI settings must not be placed in `a2aserver.conf` or `a2aclient.conf`.

See [configuration/a2ui.md](configuration/a2ui.md).

## Catalogs and mixed-catalog surfaces

A2UI presentation is catalog-driven. `a2ui.conf` declares the catalogs the agent supports and selects the default catalog for a surface. A presentation can then compose components from more than one negotiated catalog.

Agent Nebula uses the standard A2UI Basic catalog for generic layout and interaction components such as text, rows/columns, cards, buttons, text fields, choice controls, tabs, and other common UI primitives.

Agent Nebula also provides the **Agent Nebula Rich catalog**:

```text
https://agentnebula.ai/catalogs/a2ui/rich/v1/catalog.json
```

The Rich catalog contains higher-level visualization and domain presentation components such as metrics, charts, tables, status presentation, timelines, result/detail components, and Agent Nebula solution-oriented components. It complements the Basic catalog rather than duplicating Basic layout and form primitives.

A typical Agent Nebula surface therefore uses **mixed catalogs**:

```text
Surface default catalog: A2UI Basic

Column                 Basic
├── Text               Basic
├── TextField          Basic
├── Button             Basic
├── MetricGroup        Agent Nebula Rich
└── DataTable          Agent Nebula Rich
```

The surface-level default comes from the configured/default catalog. Basic components can use that default without repeating a catalog identifier. A component from the Rich catalog declares its Rich `catalogId` in `presentation.json`. Catalog selection is presentation data; it must not be implemented as Python branching in a skill handler.

This allows a single surface to combine generic A2UI controls with richer Agent Nebula components while keeping the agent's business logic independent of renderer details.

## Skill results

SecureAgent re-exports Platform `SkillResult`. A skill can return structured business data, result metadata, and an optional A2UI surface:

```python
return SkillResult(
    data={"status": "available"},
    metadata={"source": "inventory"},
    ui=surface,
)
```

SecureAgent preserves the complete `SkillResult`. Platform maps structured business data to a normal A2A DataPart and, when `ui` is present, maps the A2UI message stream to a separate A2A DataPart identified by `application/a2ui+json`.

## A2A binding

For A2A providers, Platform advertises A2UI through the official Agent Card extension mechanism using the versioned A2UI extension URI. The extension remains optional and can coexist with the Agent Nebula skill-selection extension.

For A2A clients, Platform performs A2UI extension negotiation and contributes `a2uiRendererCapabilities` metadata when the remote Agent Card advertises the supported A2UI extension. SecureAgent does not construct extension service parameters, A2A metadata, DataParts, or MIME metadata.

A2UI does not use `accepted_output_modes = ["a2ui"]`. It is carried as an A2A DataPart with the A2UI MIME type.

## Ownership

Platform owns A2UI protocol/version semantics and the A2UI-to-A2A binding. Providers own their domain-specific declarative presentation. Orchestrators should treat provider A2UI as generic presentation data, and renderer applications are responsible for rendering the declared UI.

SecureAgent deliberately does not duplicate Platform's A2UI builder, renderer, session, action, or transport implementation.

## Renderer actions

SecureAgent exposes `send_a2ui_action()` for the renderer-to-agent direction. The facade accepts transport-neutral action fields and delegates the A2A representation to Platform. Platform encodes the v1.0 `action` as an `application/a2ui+json` DataPart, activates the A2UI A2A extension, and carries `a2uiRendererDataModel` separately in message metadata when supplied.

Provider-side action callbacks are registered through `set_a2ui_action_handler()`. Action handlers are application behavior, but A2UI message parsing and dispatch remain Platform responsibilities. When an action changes only dynamic values, the provider should normally return an `updateDataModel`-style surface update through `update_a2ui_surface()` instead of rebuilding the declarative presentation.

When `want_response=True`, callers must provide `action_id`. A provider can return the corresponding v1.0 `actionResponse` and additional surface/data-model updates through `SkillResult.ui`.

## A2UI is optional

A2A-only agents do not need A2UI configuration or presentation artifacts. They return ordinary structured `SkillResult.data`. Enabling A2UI adds a presentation channel without changing the underlying business skill contract.
