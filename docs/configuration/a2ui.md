# `a2ui.conf`

Independent INI configuration owned by Agent Nebula Platform's A2UI subsystem. It is not part of `a2aserver.conf` or `a2aclient.conf`.

```ini
[a2ui]
enabled = true
version = v1.0
supported_catalog_ids =
accepts_inline_catalogs = false
```

| Field | Type | Required/default | Meaning |
|---|---|---|---|
| `a2ui.enabled` | bool | default `false` | Enable A2UI capability for the configured SecureAgent. |
| `a2ui.version` | string | default/current supported `v1.0` | A2UI protocol version processed by this Platform build. Unsupported versions are rejected. |
| `a2ui.supported_catalog_ids` | comma-separated strings | default empty | Catalog identifiers advertised/accepted by the A2UI integration. Blank entries are ignored. |
| `a2ui.accepts_inline_catalogs` | bool | default `false` | Whether the A2UI capability accepts inline catalogs. |

Unknown settings are rejected. When `a2ui_config` is not supplied to `SecureAgent`, A2UI is not configured and existing non-A2UI behavior is preserved.

Example facade configuration:

```python
agent = SecureAgent(
    config="secureagent.conf",
    a2ui_config="a2ui.conf",
)
```

SecureAgent stores the path only. Platform's `A2UIConfiguration` owns parsing, validation, version policy, and capability semantics.

For A2A, Platform maps this capability to the A2UI Agent Card extension and client renderer-capability negotiation. Those A2A binding details are not configuration fields in this file.
