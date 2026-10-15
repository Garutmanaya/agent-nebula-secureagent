# Configuration reference

SecureAgent keeps generic runtime, protocol-specific, A2UI, and Agent Nebula settings in separate files. Relative paths are resolved by the owning Platform loader relative to that configuration file unless stated otherwise.

| File | Format | Owner | Required |
|---|---|---|---|
| `secureagent.conf` | INI | Platform generic SecureAgent runtime/application configuration | Yes for standalone server composition |
| `a2aserver.conf` | TOML | Platform A2A server | For A2A server |
| `a2aclient.conf` | TOML | Platform A2A client | For A2A client |
| `a2ui.conf` | INI | Platform A2UI subsystem | No; only when A2UI is configured |
| `nebula.conf` | INI | Platform Agent Nebula integration | No |

See the dedicated pages for every field:

- [secureagent.conf](secureagent.md)
- [a2aserver.conf](a2aserver.md)
- [a2aclient.conf](a2aclient.md)
- [a2ui.conf](a2ui.md)
- [nebula.conf](nebula.md)

There is no `application.conf`. Generic runtime/application settings are owned by `secureagent.conf`.

A2UI configuration is intentionally independent from A2A configuration. Do not place `[a2ui]` settings in `a2aserver.conf` or `a2aclient.conf`.

There is intentionally no invented `mcpserver.conf` or SecureAgent REST format at this time. Configuration formats are added only when Platform owns the corresponding implementation and validation contract.

## How the files work together

`agent.py` constructs `SecureAgent` with `secureagent.conf`, then selects an A2A server or client with its corresponding configuration. `a2aserver.conf` is authoritative for the published Agent Card and skill identifiers; Python decorators bind executable handlers to those identifiers. Optional `a2ui.conf` and skill `presentation.json` provide UI capability and layout. Optional `nebula.conf` enables hosted Registry onboarding without changing the business skill code.

For a complete project layout and code example, see [Getting started](../getting-started.md).
