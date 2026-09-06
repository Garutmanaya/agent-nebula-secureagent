"""Minimal protocol-neutral SecureAgent application using the A2A server adapter."""
from agent_nebula_secureagent import ProtocolType, SecureAgent

agent = SecureAgent("application.conf", nebula_config="nebula.conf")
agent.use_protocol(ProtocolType.A2A, role="server", config="a2aserver.conf")


@agent.skill("echo", description="Return the supplied message")
async def echo(payload):
    """Implement only business behavior; infrastructure belongs to Platform."""
    return {"message": payload.get("message", "")}


if __name__ == "__main__":
    agent.run()
