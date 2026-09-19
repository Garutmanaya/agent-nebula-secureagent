# Agent Nebula A2A Schema Contract Extension

**Status:** Draft implementation profile\
**Protocol baseline:** A2A v1.0\
**Schema dialect:** JSON Schema Draft 2020-12\
**Extension profile:** A2A Schema Contract community extension Draft
0.1\
**Extension URI:** `https://w3id.org/a2a-schema-contract/draft/0.1`

## 1. Purpose

Agent Nebula uses deterministic provider agents for operations that
interact with databases, APIs, and other enterprise systems.
Natural-language interpretation belongs in the orchestrator/client layer
rather than being mandatory inside every provider agent.

For an orchestrator to convert a user request into a deterministic skill
invocation, it needs a machine-readable description of the structured
input expected by that skill. A2A v1.0 `AgentSkill` describes a
capability, but it does not define a JSON input/output schema for that
capability.

Agent Nebula therefore implements the A2A Schema Contract community
extension Draft 0.1 as an optional A2A extension. The extension
advertises structured application payload contracts without changing the
A2A v1.0 core data model.

The design has four goals:

1.  Preserve the official A2A v1.0 wire model.
2.  Keep schema publication separate from runtime skill routing.
3.  Allow generic orchestrators such as Agent Nebula Explorer to
    discover structured skill contracts.
4.  Keep provider agents deterministic and independent of an embedded
    LLM.

## 2. Why an A2A Extension

A2A defines `AgentExtension` as the protocol mechanism for optional
capabilities beyond the core specification. Agents advertise extensions
through:

`AgentCard.capabilities.extensions`

An extension declaration can provide:

-   a unique `uri`;
-   a human-readable `description`;
-   a `required` flag; and
-   extension-specific `params`.

A2A extension guidance explicitly discourages changing core protocol
structures merely to add extension-specific fields. Agent Nebula
therefore does **not** add `inputSchema`, `outputSchema`, or other
proprietary fields to the official A2A `AgentSkill`.

The schema contract is instead published through a standard
`AgentExtension`.

## 3. Architecture

``` text
User natural-language request
            |
            v
Generic orchestrator / Explorer
            |
            | Agent Card discovery
            v
Standard A2A AgentSkill
+
A2A Schema Contract extension
            |
            | JSON Schema input contract
            v
Orchestrator LLM
            |
            | schema-conforming structured payload
            v
A2A invocation
            |
            v
Deterministic provider agent
            |
            v
Database / API / enterprise system
            |
            v
Structured result + optional A2UI v1_0 surface
```

The LLM is therefore an orchestration concern. The provider agent
receives a deterministic structured request.

## 4. Relationship to A2A v1.0

The implementation preserves the A2A v1.0 model.

It does **not**:

-   modify `AgentSkill`;
-   add fields to A2A `Message`, `Task`, `Artifact`, or `Part`;
-   introduce new A2A enum values;
-   replace A2A extension negotiation;
-   use schema metadata as a proprietary transport protocol; or
-   change A2UI v1_0 messages or catalogs.

The extension is advertised using the existing A2A `AgentExtension`
mechanism.

The extension is optional in Agent Nebula P1:

``` json
{
  "uri": "https://w3id.org/a2a-schema-contract/draft/0.1",
  "required": false
}
```

A client that does not understand the extension can continue using the
standard A2A capability information. A schema-aware orchestrator can
additionally use the advertised contracts.

## 5. Relationship to Skill Selection

Schema discovery and skill selection are separate concerns.

A schema contract can associate a contract with one or more A2A skill
IDs. In the Draft 0.1 model, this association is descriptive: it tells a
client which advertised capability the contract describes.

Agent Nebula does **not** use the schema contract's `skillIds` as
runtime routing instructions.

``` text
AgentSkill.id
     |
     +---- Schema Contract
     |       describes structured payload
     |
     +---- Skill Selection extension
             selects deterministic skill at runtime
```

Agent Nebula's existing skill-selection extension remains responsible
for deterministic `AgentSkill.id` selection.

This separation prevents schema metadata from becoming an implicit
routing protocol.

## 6. Contract Identity

Every schema-constrained skill must provide an immutable, versioned
contract identifier.

Example:

``` text
https://agentnebula.ai/contracts/parking/search/v1
```

The contract identifier is distinct from the A2A skill ID.

``` text
Skill ID:
parking.search

Schema Contract ID:
https://agentnebula.ai/contracts/parking/search/v1
```

A breaking change to the structured contract should result in a new
contract version rather than silently changing the meaning of an
existing immutable identifier.

## 7. Schema Format

Agent Nebula P1 uses inline JSON Schema Draft 2020-12 for structured
`application/json` representations.

Example input schema:

``` json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "airport": {
      "type": "string",
      "description": "IATA airport code"
    },
    "startTime": {
      "type": "string",
      "format": "date-time"
    }
  },
  "required": [
    "airport"
  ],
  "additionalProperties": false
}
```

The schema should describe the actual deterministic application contract
accepted by the skill. Descriptions should be sufficiently precise for
both human clients and schema-guided LLM orchestration.

## 8. Agent Card Representation

Conceptually, an Agent Card contains standard A2A skills and a separate
Schema Contract extension:

``` json
{
  "capabilities": {
    "extensions": [
      {
        "uri": "https://w3id.org/a2a-schema-contract/draft/0.1",
        "description": "Advertises machine-readable application payload contracts using A2A Schema Contract community extension Draft 0.1.",
        "required": false,
        "params": {
          "contracts": [
            {
              "id": "https://agentnebula.ai/contracts/parking/search/v1",
              "skillIds": [
                "parking.search"
              ],
              "input": {
                "representations": [
                  {
                    "mediaType": "application/json",
                    "schema": {
                      "inline": {
                        "$schema": "https://json-schema.org/draft/2020-12/schema",
                        "type": "object",
                        "properties": {
                          "airport": {
                            "type": "string"
                          }
                        },
                        "required": [
                          "airport"
                        ],
                        "additionalProperties": false
                      }
                    }
                  }
                ]
              }
            }
          ]
        }
      }
    ]
  },
  "skills": [
    {
      "id": "parking.search",
      "name": "Search parking",
      "description": "Search available airport parking.",
      "tags": [
        "parking"
      ]
    }
  ]
}
```

The exact extension representation is generated by Agent Nebula
Platform. Application developers should not manually construct this
Agent Card extension.

## 9. SecureAgent Developer Interface

SecureAgent exposes protocol-neutral schema metadata on skill
registration.

Example:

``` python
schema = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "properties": {
        "airport": {
            "type": "string",
            "description": "IATA airport code",
        }
    },
    "required": ["airport"],
    "additionalProperties": False,
}

@agent.skill(
    "parking.search",
    schema_contract_id=(
        "https://agentnebula.ai/contracts/parking/search/v1"
    ),
    input_schema=schema,
)
async def parking_search(payload):
    ...
```

The supported declaration metadata is:

``` text
schema_contract_id
input_schema
output_schema
```

If `input_schema` or `output_schema` is declared, SecureAgent requires a
non-empty `schema_contract_id`.

SecureAgent itself remains protocol-neutral. It records the contract
metadata on the skill definition. Agent Nebula Platform's A2A adapter is
responsible for translating that metadata into the A2A Schema Contract
extension.

## 10. Platform Responsibilities

Agent Nebula Platform owns the A2A-specific representation.

During Agent Card composition, Platform:

1.  inspects registered executable skills;
2.  identifies skills with schema contract metadata;
3.  builds Draft 0.1 contract entries;
4.  associates each contract with the corresponding `AgentSkill.id`;
5.  advertises JSON representations as `application/json`;
6.  embeds the JSON Schema as an inline schema;
7.  adds the Schema Contract `AgentExtension` to
    `AgentCard.capabilities.extensions`; and
8.  leaves the standard A2A `AgentSkill` unchanged.

Skills without schema contracts continue to be advertised normally and
do not cause the Schema Contract extension to be created by themselves.

## 11. Input and Output Contracts

Input and output schemas are independent.

A skill may publish:

``` text
input schema only
output schema only
input + output schemas
```

Input contracts are particularly important for Agent Nebula Explorer
because they enable generic natural-language-to-structured-input
conversion.

Output contracts can later provide deterministic knowledge of structured
results for orchestration, validation, and workflow continuation.

## 12. Explorer Interaction Model

The intended generic Explorer flow is:

``` text
User:
"Find parking at IAD tomorrow"
          |
          v
Discover Agent Card
          |
          v
Select/identify parking.search
          |
          v
Discover parking.search schema contract
          |
          v
Explorer orchestration LLM
          |
          v
{
  "airport": "IAD",
  ...
}
          |
          v
Validate structured input
          |
          v
Invoke deterministic A2A skill
          |
          v
Structured result
          |
          +---- A2UI v1_0 surface
          |
          +---- workflow/session state
```

Explorer remains generic. It does not need hard-coded knowledge of
parking, airlines, hotels, inventory, databases, or other application
domains.

## 13. Advanced Direct Invocation

Schema contracts do not replace Agent Nebula Explorer's Advanced Direct
Invocation.

Advanced invocation remains useful when:

-   an agent does not advertise a schema contract;
-   a developer wants to test a skill directly;
-   exact structured values are already known; or
-   orchestration/LLM behavior needs to be bypassed for diagnostics.

``` text
Interactive workflow:
Natural language -> schema -> orchestrator LLM -> structured payload -> agent

Advanced invocation:
Developer JSON -> optional schema validation -> agent
```

A generic orchestrator should not guess an undocumented deterministic
payload contract.

## 14. Relationship to A2UI v1_0

The Schema Contract extension and A2UI solve different problems.

``` text
Schema Contract
    What structured data does a skill accept/produce?

A2A
    How do client and agent communicate and execute work?

A2UI
    How does an agent describe interactive UI, state, and actions?
```

Agent Nebula does not modify A2UI v1_0 to carry skill input schemas.

An agent can therefore advertise:

-   standard A2A skills;
-   the A2A Schema Contract extension;
-   the Agent Nebula skill-selection extension; and
-   the A2UI v1.0 extension.

These capabilities remain independently defined and negotiated.

## 15. Relationship to MCP

MCP provides useful precedent for schema-driven model invocation. MCP
tools expose `inputSchema`, and current MCP specifications use JSON
Schema with JSON Schema 2020-12 as the default dialect.

The conceptual mapping is:

``` text
MCP                              Agent Nebula / A2A

Tool                             AgentSkill
Tool.name                        AgentSkill.id
Tool.description                 AgentSkill.description
Tool.inputSchema                 Schema Contract input representation
Tool.outputSchema                Schema Contract output representation
LLM tool argument generation     Explorer LLM input mapping
tools/call                       A2A invocation
```

Agent Nebula does not convert A2A skills into MCP tools. MCP is
referenced as evidence that machine-readable JSON Schema is a practical
interface between an LLM orchestrator and deterministic operations.

## 16. P1 Scope

P1 intentionally implements only schema contract declaration and Agent
Card advertisement.

Included:

-   Schema Contract Draft 0.1 extension URI;
-   standard A2A `AgentExtension` advertisement;
-   inline JSON Schema contracts;
-   JSON Schema Draft 2020-12 declarations;
-   `application/json` representations;
-   contract-to-skill association;
-   SecureAgent `schema_contract_id`;
-   SecureAgent `input_schema`;
-   SecureAgent `output_schema`; and
-   automatic Platform Agent Card composition.

Not included in P1:

-   remote schema/catalog resolution;
-   network dereferencing of JSON Schema `$ref`;
-   schema contract activation metadata;
-   primary-Part metadata;
-   request-boundary schema validation;
-   response-boundary schema validation;
-   Explorer LLM orchestration changes;
-   workflow sequencing;
-   A2UI action changes; or
-   application-specific schemas for Solutions/Playground.

These capabilities should be implemented independently as later phases
rather than approximated through proprietary A2A fields.

## 17. Security Considerations

Schema publication is metadata; it does not weaken the existing Agent
Nebula authentication, authorization, policy, or transport controls.

Clients must treat remote schemas as untrusted input.

In particular:

-   validate schema documents before use;
-   enforce reasonable schema/document size and complexity limits;
-   do not automatically fetch arbitrary network `$ref` targets;
-   do not treat schema validation as authorization;
-   continue normal OAuth/API-key/mTLS/policy enforcement;
-   validate generated structured arguments before invoking
    deterministic operations; and
-   do not infer runtime routing solely from schema `skillIds`.

MCP's JSON Schema work independently calls out network `$ref`
dereferencing as an SSRF/fetch-amplification risk. Agent Nebula P1
avoids this class of problem by supporting inline schemas only.

## 18. Versioning and Compatibility

There are three independent versions to keep distinct:

``` text
A2A protocol version
    v1.0

Schema Contract extension version
    Draft 0.1

Application contract version
    e.g. /contracts/parking/search/v1
```

A breaking application schema change should create a new application
contract ID.

A breaking Schema Contract extension revision should use the URI defined
by the corresponding extension specification.

Neither should require modification of the underlying A2A v1.0
structures.

## 19. Current Status

The Schema Contract specification referenced by Agent Nebula is a
community draft, not a normative feature of the A2A v1.0 core
specification.

Agent Nebula therefore treats it as an optional, isolated extension
profile. The implementation should remain modular so it can track
upstream changes without changing application business logic or
introducing proprietary fields into standard A2A structures.

## 20. References

1.  **A2A Protocol --- Extensions**\
    https://a2a-protocol.org/dev/topics/extensions/

2.  **A2A Protocol --- Specification**\
    https://a2a-protocol.org/dev/specification/

3.  **A2A Protocol --- GitHub extension guidance**\
    https://github.com/a2aproject/A2A/blob/main/docs/topics/extensions.md

4.  **A2A Schema Contract community extension Draft 0.1**\
    Extension identifier:\
    https://w3id.org/a2a-schema-contract/draft/0.1

5.  **A2A Schema Contract proposal / discussion**\
    https://github.com/a2aproject/A2A/issues/2180

6.  **Model Context Protocol --- Tools**\
    https://modelcontextprotocol.io/specification/draft/server/tools

7.  **MCP SEP-1613 --- JSON Schema 2020-12 default dialect**\
    https://modelcontextprotocol.io/seps/1613-establish-json-schema-2020-12-as-default-dialect-f

## 21. Design Principle

The core Agent Nebula rule is:

> **Natural language belongs at the orchestration boundary;
> deterministic agents publish machine-readable contracts and execute
> validated structured operations.**

The Schema Contract extension provides the discovery metadata required
to preserve that boundary while remaining within A2A's defined extension
architecture.
