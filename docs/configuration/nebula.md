# `nebula.conf`

Optional INI configuration for Agent Nebula Registry integration. It is independent of A2A endpoint security.

```ini
[nebula]
base_url = https://nebula.example
timeout_seconds = 30

[tls]
mode = full-verify
ca_file = certs/trust-bundle.pem
client_certificate_file = certs/client.crt
client_private_key_file = secrets/client.key

[registration]
enabled = true
authentication = API_KEY
api_key_file = secrets/onboarding-api-key
state_key = nebula-registration
retry_count = 3
retry_delay_seconds = 1.0
resolve_before_register = true
```

| Field | Type | Required/default | Meaning |
|---|---|---|---|
| `nebula.base_url` | string | required | Registry base URL. |
| `nebula.timeout_seconds` | number | default `30`, >0 and <=300 | Registry request timeout. |
| `tls.mode` | string | default/only `full-verify` | TLS verification policy; disabling verification is not supported. |
| `tls.ca_file` | path | required | CA/trust file. |
| `tls.client_certificate_file` | path | optional* | Client certificate; must pair with private key. |
| `tls.client_private_key_file` | path | optional* | Client private key; must pair with certificate. |
| `registration.enabled` | bool | default `true` | Enable registration lifecycle. |
| `registration.authentication` | enum | default `OPEN` | `OPEN` or `API_KEY`. |
| `registration.api_key_file` | path | required only for `API_KEY` | API key file. Forbidden for `OPEN`. |
| `registration.state_key` | string | default `nebula-registration` | Nonblank persisted registration-state key. |
| `registration.retry_count` | int | default `3`, 1..20 | Registration attempts. |
| `registration.retry_delay_seconds` | number | default `1.0`, 0..60 | Delay between retries. |
| `registration.resolve_before_register` | bool | default `true` | Resolve prior registration state before registering. |
