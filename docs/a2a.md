# A2A

SecureAgent's A2A adapter is intentionally thin. It adapts registered protocol-neutral `SkillDefinition` objects to Platform's executable-skill contract and delegates the complete A2A composition to `A2AStandaloneApplicationComposer` in Agent Nebula Platform.

Platform loads the official A2A Agent Card, validates executable skills against published `AgentSkill.id` values, creates the official `DefaultRequestHandler`/task store/executor bridge, composes OAuth protected-resource validation when required, configures the A2A listener, and optionally enables Agent Nebula onboarding.

SecureAgent does not parse Agent Cards, implement the Agent Nebula A2A skill-selection extension, select OAuth schemes, validate access tokens/DPoP proofs, implement JSON-RPC/HTTP+JSON/gRPC bindings, or add fields to official A2A models. Those responsibilities remain in Platform and the official A2A SDK.

## Multiple skills

A SecureAgent A2A server may register one or more business skills with `@agent.skill(...)`. SecureAgent passes all registered skills to Platform without selecting or routing between them.

For a multi-skill provider, Platform advertises the Agent Nebula A2A skill-selection extension as required and deterministically dispatches the client-selected, advertised `AgentSkill.id`. For a single-skill provider, Platform advertises the same extension as optional so ordinary A2A clients remain compatible. The extension uses official A2A extension and metadata facilities; SecureAgent does not maintain a duplicate implementation of that contract.

Every executable SecureAgent skill must have a corresponding `agent_card.skills[].id` in `a2aserver.conf`. Platform owns this validation and fails composition when the executable and published skill sets are inconsistent.

Skill-specific security requirements also remain a Platform concern. A Nebula-aware client can select a skill before invocation so Platform can resolve the corresponding security requirements and acquire least-privilege authorization. The provider validates authorization before the selected business handler is reached.

A2A client functionality exists in Platform (`A2AClientServiceFactory`/`A2AClientAdapter`) and remains a Platform capability. The common SecureAgent protocol model already distinguishes client/server roles; a future public client facade should delegate to that service rather than reproduce it.
