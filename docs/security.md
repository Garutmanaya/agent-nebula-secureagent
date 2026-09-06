# Security boundary

SecureAgent selects secure defaults but does not implement cryptography or standards protocols.

- SecureAgent: developer intent, required skill scopes, protocol selection.
- Platform: Agent Card security interpretation, OAuth client/protected-resource composition, A2A security negotiation, TLS policy, Registry integration, plugin lifecycle.
- SDK: reusable OAuth/JWT/JWK/JOSE/DPoP and RFC-level primitives.

A trust bundle means TLS trust material is available; it does not by itself enable mutual TLS. mTLS is enabled only when the applicable protocol/security configuration explicitly requires a client identity or mTLS scheme.

Never put secret values in Agent Card/configuration fields intended for metadata. Configuration points to secret files where required.
