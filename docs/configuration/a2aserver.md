# `a2aserver.conf`

TOML file owned by Platform's A2A server module. `[agent_card]` is converted directly to the official A2A 1.0 `AgentCard`; SecureAgent does not maintain a parallel Agent Card model.

## Listener fields

```toml
[server]
host = "0.0.0.0"
port = 9999
tls_certificate_file = "certs/server.crt"
tls_private_key_file = "secrets/server.key"
tls_trust_bundle_file = "certs/trust-bundle.pem"
```

| Field | Type | Required | Default | Meaning |
|---|---|---:|---|---|
| `server.host` | string | no | `0.0.0.0` | Listener bind address. |
| `server.port` | integer | no | `9999` | Listener port. |
| `server.tls_certificate_file` | path | no* | — | Server certificate. Must be paired with private key. |
| `server.tls_private_key_file` | path | no* | — | Server private key. Must be paired with certificate. |
| `server.tls_trust_bundle_file` | path | no | — | Trust bundle used where the A2A security composition requires trusted CA material. Presence alone does not mean mTLS. |

## Agent Card fields

The Platform template supports the official A2A 1.0 Agent Card structure:

| Field | Type | Meaning |
|---|---|---|
| `agent_card.name` | string | Agent display/name identity. |
| `agent_card.description` | string | Human-readable description. |
| `agent_card.version` | string | Agent version. |
| `agent_card.documentation_url` | string | Documentation URL. |
| `agent_card.icon_url` | string | Icon URL. |
| `agent_card.default_input_modes` | list[string] | Default accepted media/mode values. |
| `agent_card.default_output_modes` | list[string] | Default output media/mode values. |
| `agent_card.provider.organization` | string | Provider organization. |
| `agent_card.provider.url` | string | Provider URL. |
| `agent_card.supported_interfaces[].url` | string | Public interface URL/address. First entry is preferred by current composition. |
| `agent_card.supported_interfaces[].protocol_binding` | string | `JSONRPC`, `HTTP+JSON`, or `GRPC` as supported by official A2A. |
| `agent_card.supported_interfaces[].protocol_version` | string | Protocol version, normally `1.0`. |
| `agent_card.supported_interfaces[].tenant` | string | Optional tenant metadata. |
| `agent_card.capabilities.streaming` | boolean | Advertises streaming capability. |
| `agent_card.capabilities.push_notifications` | boolean | Advertises push notification capability. |
| `agent_card.capabilities.extended_agent_card` | boolean | Advertises extended Agent Card capability. |
| `agent_card.capabilities.extensions[].uri` | string | Extension identifier URI. |
| `...extensions[].description` | string | Extension description. |
| `...extensions[].required` | boolean | Whether the extension is required. |
| `...extensions[].params` | table | Extension-specific parameters. |
| `agent_card.skills[].id` | string | Published skill identifier; each executable SecureAgent A2A skill must have a matching published identifier. |
| `agent_card.skills[].name` | string | Published skill name. |
| `agent_card.skills[].description` | string | Published skill description. |
| `agent_card.skills[].tags` | list[string] | Discovery tags. |
| `agent_card.skills[].examples` | list[string] | Example requests. |
| `agent_card.skills[].input_modes` | list[string] | Skill-specific input modes. |
| `agent_card.skills[].output_modes` | list[string] | Skill-specific output modes. |
| `agent_card.signatures[].protected` | string | Precomputed JWS protected value when configured. |
| `agent_card.signatures[].signature` | string | Precomputed signature value. |
| `agent_card.signatures[].header` | table | JWS header, e.g. `kid`. |

## Security schemes

Security scheme keys (`api_key`, `oauth2`, etc.) are arbitrary identifiers referenced by security requirements.

- `api_key_security_scheme`: `description`, `location`, `name`.
- `http_auth_security_scheme`: `description`, `scheme`, `bearer_format`.
- `oauth2_security_scheme`: `description`, `oauth2_metadata_url`, plus `flows`.
- `open_id_connect_security_scheme`: `description`, `open_id_connect_url`.
- `mtls_security_scheme`: `description`.

OAuth flows represented by A2A 1.0 include `authorization_code`, `client_credentials`, `implicit`, `password`, and `device_code`. Flow fields include the applicable `authorization_url`, `device_authorization_url`, `token_url`, `refresh_url`, `pkce_required`, and `scopes` map. Deprecated flows should be omitted unless interoperability requires them.

`[[agent_card.security_requirements]]` defines OR alternatives. Its `schemes` table maps scheme names to required scope lists. Multiple scheme entries inside one `schemes` map form an AND requirement. The same structure may appear under `[[agent_card.skills.security_requirements]]`.

SecureAgent does not reinterpret these security declarations; Platform does.


## Skill publication and multi-skill behavior

SecureAgent passes all registered A2A business skills to Platform. Each registered `@agent.skill("...")` identifier must therefore correspond to an `agent_card.skills[].id` in this file. Platform validates the published/executable relationship during composition; SecureAgent does not duplicate that validation.

When more than one executable skill is configured, Platform advertises the Agent Nebula A2A skill-selection extension as required and uses the client-selected `AgentSkill.id` for deterministic dispatch. With one executable skill, the extension is optional. Extension declaration, request metadata parsing, dispatch validation, and skill-specific security enforcement are Platform responsibilities rather than `a2aserver.conf` or SecureAgent responsibilities.

## A2UI boundary

A2UI settings do not belong in `a2aserver.conf`. Configure A2UI independently in `a2ui.conf` and pass that file through `SecureAgent(a2ui_config=...)`.

When enabled, Platform's isolated A2UI/A2A extension adapter contributes the A2UI capability to the official Agent Card. The A2A server configuration does not parse or own A2UI version, catalog, renderer-capability, or DataPart semantics.
