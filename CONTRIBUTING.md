# Contributing

Keep SecureAgent thin. Protocol implementation, security enforcement, transport routing, lifecycle, and Agent Nebula integration belong in `agent-nebula-platform`; RFC/cryptographic primitives belong in `agent-nebula-sdk`. Add a SecureAgent protocol adapter only after Platform exposes the corresponding protocol composition contract.

Run `make lint` and `make test` before submitting changes.
