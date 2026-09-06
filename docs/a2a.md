# A2A

SecureAgent's A2A adapter is intentionally thin. It delegates to `A2AStandaloneApplicationComposer` in Agent Nebula Platform. Platform loads the official A2A Agent Card, validates that the configured business skill is published, creates the official `DefaultRequestHandler`/task store/executor bridge, composes OAuth protected-resource validation when the Agent Card requires it, configures the A2A listener, and optionally enables Agent Nebula onboarding.

SecureAgent does not parse Agent Cards, select OAuth schemes, validate access tokens/DPoP proofs, implement JSON-RPC/HTTP+JSON/gRPC bindings, or invent A2A message fields.

The current server composition requires exactly one business skill because A2A 1.0 `SendMessage` does not define a standard skill identifier. This restriction is preferable to proprietary routing metadata.

A2A client functionality exists in Platform (`A2AClientServiceFactory`/`A2AClientAdapter`) and remains a Platform capability. The common SecureAgent protocol model already distinguishes client/server roles; a public client facade should delegate to that service rather than reproduce it.
