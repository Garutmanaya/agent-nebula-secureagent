# Configuration reference

SecureAgent keeps protocol-neutral, protocol-specific, and Agent Nebula settings in separate files. Relative paths are resolved by the owning Platform loader relative to that configuration file unless stated otherwise.

| File | Format | Owner | Required |
|---|---|---|---|
| `secureagent.conf` | INI | Platform application configuration | Yes for standalone server composition |
| `a2aserver.conf` | TOML | Platform A2A server | For A2A server |
| `a2aclient.conf` | TOML | Platform A2A client | For A2A client |
| `nebula.conf` | INI | Platform Agent Nebula integration | No |

See the dedicated pages for every field:

- [secureagent.conf](application.md)
- [a2aserver.conf](a2aserver.md)
- [a2aclient.conf](a2aclient.md)
- [nebula.conf](nebula.md)

There is intentionally no invented `mcpserver.conf` or SecureAgent REST format at this time. Configuration formats are added only when Platform owns the corresponding implementation and validation contract.
