# Agent Nebula SecureAgent — A2A Frozen Requirements

This directory is the application-facing A2A facade. All code here MUST follow these requirements.

## Frozen ownership

1. `a2a-sdk` owns standard A2A models, execution, client operations, tasks, artifacts, streaming, cancellation, push notifications, and protocol bindings.
2. `agent_nebula_platform.a2a` is the only Agent Nebula Platform A2A dependency allowed here.
3. Code in this directory MUST NOT import `agent_nebula_platform.protocols.*` or `agent_nebula_secureagent.protocols.*`.
4. SecureAgent adds only configuration-based construction, native `AgentExecutor` registration, lifecycle convenience, and delegation to Platform A2A integration.
5. Public A2A boundaries use native `a2a-sdk` types. Do not create SecureAgent Message, Task, Artifact, RequestContext, EventQueue, or Client wrappers.
6. Agent Card is authoritative for skills, interfaces, extensions, and security.
7. Nebula-specific extension semantics come only from `agent_nebula_platform.a2a.extensions`.
8. A2UI does not belong in this directory or in the SecureAgent A2A facade.
9. No LLM-dependent protocol behavior is allowed.
10. Configuration, credentials, secrets, and mutable runtime state remain external.

## Frozen structure

```text
a2a/
├── README.md
├── __init__.py
├── client.py
└── server.py
```

Do not add adapters, services, factories, interfaces, models, or compatibility layers without changing this contract first.

## Coding standards

- Keep the facade thin and direct.
- Prefer native SDK types in signatures and return values.
- Do not duplicate Platform configuration, security, or extension logic.
- Do not import legacy A2A implementation paths.
- Do not add A2UI helpers.
- Do not convert native SDK objects to dictionaries merely to hide the SDK.
- Use explicit type hints and explicit imports.
- Keep exports minimal.
- Comments explain Agent Nebula-specific behavior, not Python syntax.
- Fail explicitly on invalid or ambiguous configuration.
- Tests validate the public boundary.
