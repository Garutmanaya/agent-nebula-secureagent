# Agent Nebula Enterprise Registry Hub

[Agent Nebula](https://agentnebula.ai) is an optional hosted integration for SecureAgent applications. It adds an enterprise A2A Registry, discovery, Explorer, Playground, OAuth, policy services, and account management. **SecureAgent agents can run without it** using standard A2A interfaces.

## Account and agent ownership

```text
Publisher (account / organization)
  └── Provider (agent publisher identity)
        └── Agents (registered A2A endpoints and Agent Cards)
```

A developer first creates an account, configures the provider identity and required onboarding credentials, and then registers an agent. The exact UI and credential workflow is documented in the [registration example](https://github.com/garutmanaya/agent-nebula-secureagent-examples/tree/main/examples-nebula/06-nebula-registration-discovery) and the [integration examples guide](https://github.com/garutmanaya/agent-nebula-secureagent-examples/tree/main/examples-nebula).

## Registration and discovery

`nebula.conf` configures optional Registry integration separately from `a2aserver.conf`. Platform prepares registration metadata from the agent's configured identity and standard Agent Card URI and performs onboarding according to its configured authentication and TLS policy. The Registry must be able to retrieve the advertised Agent Card for URI-based registration. Local-only URLs are not reachable from a remote hosted Registry.

A public HTTPS endpoint (for example, a developer tunnel in front of Nginx) can expose a locally running agent for Registry and Explorer access. The public Agent Card and A2A interface addresses must agree with the externally reachable routes. See the [examples repository](https://github.com/garutmanaya/agent-nebula-secureagent-examples) for the Nginx/ngrok setup.

## OAuth-scoped and policy-controlled invocation

OAuth and authorization are distinct from Registry registration. Registering an Agent Card does not automatically make an agent accessible to every caller or configure a policy. The agent's security requirements, OAuth client credentials, requested scopes, and applicable policy must align before an invocation can succeed.

```text
Client → obtain token with permitted scopes → discover Agent Card
       → invoke protected A2A skill → Platform validates access
       → execute or deny based on authentication, scopes and policy
```

Use the [OAuth and scope examples](https://github.com/garutmanaya/agent-nebula-secureagent-examples/tree/main/examples-nebula) to exercise permitted and rejected requests. Hosted Explorer requires network access to the agent; registering a localhost-only endpoint does not provide that connectivity.

## Further reading

- [SecureAgent configuration reference](configuration/README.md)
- [Security and authorization](security.md)
- [Standalone and hosted examples](https://github.com/garutmanaya/agent-nebula-secureagent-examples)
