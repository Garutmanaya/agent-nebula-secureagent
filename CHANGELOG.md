# Changelog

## Unreleased

- Restored direct A2A client capability through the new protocol-neutral SecureAgent adapter boundary.
- Added Agent Card resolution, direct message invocation, deterministic `skill_id` forwarding, and simultaneous A2A server/client configuration.
- Kept all A2A transport, security, extension, and wire-model behavior in Agent Nebula Platform.

- Added SecureAgent A2A multi-skill composition by passing all registered business skills to Platform.
- Removed the obsolete SecureAgent single-skill restriction; Platform owns deterministic skill selection and dispatch through the Agent Nebula A2A extension.
- Updated A2A architecture and configuration documentation for multi-skill publication and repository boundaries.

## 0.1.0

- Introduced the protocol-neutral `SecureAgent` facade.
- Reused Platform skill models rather than Connect-specific runtime composition.
- Added adapter registry and A2A server adapter backed by Platform.
- Added comprehensive API and configuration documentation.

## P1 client/discovery restoration

- Restored Agent Nebula provider discovery through a Platform-owned Registry client.
- Added stable `DiscoveredAgent` and `DiscoveredSkill` facade models.
- Added discovered-provider A2A invocation with Registry resource propagation,
  optional deterministic `skill_id`, and Platform-owned OAuth/DPoP negotiation.
- Added deterministic SecureAgent server application cleanup.
