# A2UI

A2UI is a Platform presentation capability, not a transport-specific SecureAgent type. Platform owns A2UI surfaces, validation, action binding, sessions, negotiation, and rendering contracts.

The generic Platform `SkillResult` can carry an A2UI surface. SecureAgent re-exports `SkillResult`, allowing future facade helpers to expose A2UI without coupling business skills to A2A, REST, or MCP. This initial facade intentionally does not duplicate the extensive A2UI builder/session API already owned by Platform.
