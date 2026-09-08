# A2UI

SecureAgent exposes A2UI as an optional presentation capability while Agent Nebula Platform owns the A2UI protocol implementation. A2UI is not a separate SecureAgent transport and does not introduce a separate endpoint or security path.

The current Platform implementation targets A2UI `v1.0`. Version-specific A2UI models, validation, surfaces, actions, sessions, and capability negotiation remain in Platform so that a future A2UI version can be updated without changing business skills or the SecureAgent facade.

## Configuration boundary

A2UI configuration is independent from A2A configuration:

```text
secureagent.conf   -> generic SecureAgent runtime/application settings
a2aserver.conf     -> A2A server and Agent Card
a2aclient.conf     -> A2A client transport/security preferences
a2ui.conf          -> A2UI protocol capabilities
nebula.conf         -> optional Agent Nebula Registry integration
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

Platform owns A2UI protocol/version semantics and the A2UI-to-A2A binding. Providers own their domain-specific A2UI presentation. Orchestrators should treat provider A2UI as generic presentation data, and renderer applications are responsible for rendering the declared UI.

SecureAgent deliberately does not duplicate Platform's A2UI builder, renderer, session, action, or transport implementation.
