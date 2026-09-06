# `a2aclient.conf`

This is the complete field set currently accepted by Platform's dedicated A2A client loader.

```toml
[client]
streaming = true
polling = false
supported_protocol_bindings = ["JSONRPC", "HTTP+JSON"]
use_client_preference = false
accepted_output_modes = ["application/json"]
timeout_seconds = 30
agent_card_path = "/.well-known/agent-card.json"

[client.tls]
trust_bundle = "certs/trust-bundle.pem"
certificate_file = "certs/client.crt"
private_key_file = "secrets/client.key"

[client.credentials.my_api_key]
secret_file = "secrets/api-key"

[client.oauth]
client_id_file = "secrets/client-id"
authentication_private_key_file = "secrets/oauth-auth.key"
dpop_private_key_file = "secrets/dpop.key"
key_id = "a2a-oauth-client"
algorithm = "ES256"
```

| Field | Type | Required/default | Meaning |
|---|---|---|---|
| `client.streaming` | bool | default `true` | Enable streaming preference. |
| `client.polling` | bool | default `false` | Enable polling behavior. |
| `client.supported_protocol_bindings` | list[string] | required, non-empty | Allowed official bindings: `JSONRPC`, `HTTP+JSON`, `GRPC`; entries must be unique. |
| `client.use_client_preference` | bool | default `false` | Let client preference influence interface selection. |
| `client.accepted_output_modes` | list[string] | default empty | Accepted output modes. |
| `client.timeout_seconds` | number | default `30.0`, >0 | Outbound timeout. |
| `client.agent_card_path` | string | optional | Nonblank Agent Card discovery path override. |
| `client.tls.trust_bundle` | path | optional | Existing CA/trust file for outbound TLS. |
| `client.tls.certificate_file` | path | optional* | Existing client certificate; pair with private key. |
| `client.tls.private_key_file` | path | optional* | Existing client private key; pair with certificate. |
| `client.credentials.<scheme>.secret_file` | path | optional/repeatable | Existing local secret for the exact remote Agent Card scheme name. |
| `client.oauth.client_id_file` | path | required when `[client.oauth]` exists | Client-id persistence destination; parent directory must exist. |
| `client.oauth.authentication_private_key_file` | path | required with OAuth | Existing OAuth client-authentication private key. |
| `client.oauth.dpop_private_key_file` | path | required with OAuth | Existing DPoP private key. |
| `client.oauth.key_id` | string | default `a2a-oauth-client` | Nonblank key identifier. |
| `client.oauth.algorithm` | string | default `ES256` | Nonblank configured algorithm. |

When OAuth configuration is present and the remote Agent Card advertises OAuth, Platform can perform discovered OAuth client registration/token acquisition according to its A2A client implementation. SecureAgent does not implement this flow itself.
