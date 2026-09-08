# Skills

Skills are protocol-neutral application behavior. SecureAgent converts decorator metadata into Platform `SkillDefinition` objects rather than defining a second runtime skill hierarchy.

By default the skill identifier is also the required OAuth scope. This preserves fail-closed behavior for transports that enforce OAuth. A handler receives a plain mapping payload for the concise developer experience.

A handler may return either a mapping or Platform `SkillResult`. Mapping output is normalized to `SkillResult(data=...)`. SecureAgent preserves an explicit `SkillResult` intact across the facade-to-Platform boundary:

```text
SkillResult
├── data       structured business result
├── metadata   result/application metadata
└── ui         optional A2UI surface
```

For A2A, Platform owns mapping these channels to official response parts. SecureAgent does not serialize A2UI or A2A DataParts itself.

Input/output schemas are metadata contracts and should be valid JSON Schema documents appropriate to the application. Protocol adapters decide how those contracts are published by their protocol; SecureAgent does not encode A2A-specific `AgentSkill` objects in the generic skill API.
