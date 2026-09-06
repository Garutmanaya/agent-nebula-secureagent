# Skills

Skills are protocol-neutral application behavior. SecureAgent converts decorator metadata into Platform `SkillDefinition` objects rather than defining a second runtime skill hierarchy.

By default the skill identifier is also the required OAuth scope. This preserves fail-closed behavior for transports that enforce OAuth. A handler receives a plain mapping payload for the concise developer experience; SecureAgent converts mapping output to Platform `SkillResult`.

Input/output schemas are metadata contracts and should be valid JSON Schema documents appropriate to the application. Protocol adapters decide how those contracts are published by their protocol; SecureAgent does not encode A2A-specific AgentSkill objects in the generic skill API.
