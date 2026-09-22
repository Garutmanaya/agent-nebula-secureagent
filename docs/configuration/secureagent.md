# `secureagent.conf`

INI file containing only generic application identity/filesystem ownership used by the current SecureAgent A2A composition.

```ini
[runtime.application]
name = inventory-agent
product_root = /opt/agent-nebula/inventory-agent
runtime_root = /run/agent-nebula/inventory-agent
console_logging = true
log_level = INFO
metrics = false
telemetry = false
```

| Field | Type | Required | Default | Meaning |
|---|---|---:|---|---|
| `runtime.application.name` | string | yes | — | Stable local application name. Blank values are rejected. |
| `runtime.application.product_root` | path | yes | — | Persistent/product-owned root. Relative values resolve against `secureagent.conf`. |
| `runtime.application.runtime_root` | path | yes | — | Disposable runtime root. Relative values resolve against `secureagent.conf`. |
| `runtime.application.console_logging` | boolean | no | `true` | Enable the standalone console log handler. |
| `runtime.application.log_level` | string | no | `INFO` | Console log level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |
| `runtime.application.metrics` | boolean | no | `false` | Enable Platform metrics for the standalone runtime. |
| `runtime.application.telemetry` | boolean | no | `false` | Enable Platform telemetry for the standalone runtime. |

Protocol and presentation fields do not belong in this file. A2A details belong in `a2aserver.conf`/`a2aclient.conf`; A2UI details belong in `a2ui.conf`; Registry integration belongs in `nebula.conf`. The optional A2UI file is referenced through `SecureAgent(a2ui_config=...)`, not embedded in `secureagent.conf`.
