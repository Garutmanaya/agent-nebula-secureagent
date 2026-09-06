# Agent Nebula integration

Agent Nebula Registry integration is optional. `nebula.conf` is supplied to `SecureAgent` separately from protocol configuration. For A2A server composition, Platform converts Registry settings into onboarding settings and a registration payload containing the agent identity, standard Agent Card URI, A2A protocol declaration, and published capabilities.

The Registry is not required for pure A2A interoperability. It adds enterprise registration/discovery and lifecycle integration. A2A OAuth security remains endpoint security derived from the Agent Card; it is not Registry authentication.
