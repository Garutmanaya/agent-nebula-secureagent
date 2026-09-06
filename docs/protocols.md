# REST and MCP

## REST

Platform already contains a transport-neutral REST skill adapter and FastAPI runtime integration. SecureAgent recognizes `ProtocolType.REST`, but this repository does not yet publish a REST server adapter/configuration because the public facade should not invent a second configuration model around Platform's existing preset settings. When added, the adapter must consume the same `SkillDefinition` objects used by A2A.

## MCP

`ProtocolType.MCP` reserves the public protocol identity, but Platform does not currently implement an MCP protocol module. SecureAgent therefore fails explicitly if MCP server composition is requested. This is a capability boundary, not a hidden fallback to REST or A2A.

The intended extension path is: implement the MCP protocol plugin/composer in Platform first, then register a thin `ServerProtocolAdapter` in SecureAgent. The business skill API remains unchanged.
