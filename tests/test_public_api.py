from pathlib import Path

import asyncio

import pytest

from agent_nebula_secureagent import ProtocolType, SecureAgent
from agent_nebula_secureagent.exceptions import (
    SecureAgentConfigurationError,
    SecureAgentProtocolError,
)
from agent_nebula_secureagent.protocols.a2a import A2AServerProtocolAdapter


class _RecordingA2AComposer:
    """Capture the SecureAgent-to-Platform composition boundary for unit tests."""

    arguments: dict[str, object] = {}

    def compose(self, **kwargs):
        """Record composition arguments without invoking Platform infrastructure."""
        type(self).arguments = dict(kwargs)
        return object()


def _compose_a2a_with_registered_skills(monkeypatch, agent: SecureAgent) -> dict[str, object]:
    """Compose through the A2A adapter and return arguments delegated to Platform."""
    monkeypatch.setattr(
        "agent_nebula_secureagent.protocols.a2a.A2AStandaloneApplicationComposer",
        _RecordingA2AComposer,
    )
    A2AServerProtocolAdapter().compose(
        application_config=Path("secureagent.conf"),
        protocol_config=Path("a2aserver.conf"),
        nebula_config=None,
        skills=agent.skills,
    )
    return _RecordingA2AComposer.arguments


def test_secureagent_default_configuration_filename() -> None:
    agent = SecureAgent()
    assert agent._application_config == Path("secureagent.conf")


def test_secureagent_accepts_user_selected_configuration_filename(tmp_path: Path) -> None:
    config = tmp_path / "my-agent.conf"
    agent = SecureAgent(config=config)
    assert agent._application_config == config


def test_common_protocol_api_does_not_require_a2a_specific_secure_agent() -> None:
    agent = SecureAgent("secureagent.conf")
    agent.use_protocol("a2a", role="server", config="a2aserver.conf")
    assert agent.protocols[0].protocol is ProtocolType.A2A


def test_skill_defaults_scope_to_skill_identifier() -> None:
    agent = SecureAgent()

    @agent.skill("inventory.lookup")
    def lookup(payload):
        return payload

    assert agent.skills[0].required_scopes == ("inventory.lookup",)


def test_duplicate_protocol_role_is_rejected() -> None:
    agent = SecureAgent()
    agent.use_protocol("a2a", role="server", config="a.conf")
    with pytest.raises(SecureAgentConfigurationError):
        agent.use_protocol("a2a", role="server", config="b.conf")


def test_unimplemented_protocol_fails_explicitly() -> None:
    agent = SecureAgent()
    agent.use_protocol("mcp", role="server", config="mcp.conf")

    @agent.skill("echo")
    def echo(payload):
        return payload

    with pytest.raises(SecureAgentProtocolError):
        agent.compose()


def test_a2a_adapter_passes_all_registered_skills_to_platform(monkeypatch) -> None:
    agent = SecureAgent()

    @agent.skill("general.hello")
    def hello(payload):
        return payload

    @agent.skill("inventory.lookup")
    def lookup(payload):
        return payload

    delegated = _compose_a2a_with_registered_skills(monkeypatch, agent)

    assert tuple(skill.skill_id for skill in delegated["skills"]) == (
        "general.hello",
        "inventory.lookup",
    )
    assert "skill" not in delegated


def test_a2a_adapter_preserves_single_skill_composition(monkeypatch) -> None:
    agent = SecureAgent()

    @agent.skill("general.hello")
    def hello(payload):
        return payload

    delegated = _compose_a2a_with_registered_skills(monkeypatch, agent)

    assert tuple(skill.skill_id for skill in delegated["skills"]) == ("general.hello",)


class _RecordingClientAdapter:
    """Capture the SecureAgent client boundary without invoking A2A infrastructure."""

    protocol = ProtocolType.A2A
    calls: list[tuple[str, dict[str, object]]] = []

    async def resolve_remote(self, **kwargs):
        type(self).calls.append(("resolve", dict(kwargs)))
        return {"name": "remote-agent"}

    async def send_message(self, **kwargs):
        type(self).calls.append(("send", dict(kwargs)))
        return ({"message": "ok"},)


def _client_registry():
    from agent_nebula_secureagent.protocols import ProtocolAdapterRegistry

    _RecordingClientAdapter.calls = []
    return ProtocolAdapterRegistry(client_adapters=(_RecordingClientAdapter(),))


def test_secureagent_resolves_agent_card_through_configured_client() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    card = asyncio.run(agent.resolve_agent_card("https://provider.example"))

    assert card == {"name": "remote-agent"}
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "resolve"
    assert arguments["protocol_config"] == Path("a2aclient.conf")
    assert arguments["target"] == "https://provider.example"


def test_secureagent_sends_selected_skill_through_configured_client() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    result = asyncio.run(agent.send_message_to(
        "https://provider.example",
        data={"sku": "ABC"},
        skill_id="inventory.lookup",
    ))

    assert result == ({"message": "ok"},)
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "send"
    assert arguments["skill_id"] == "inventory.lookup"
    assert arguments["data"] == {"sku": "ABC"}


def test_server_and_client_roles_can_be_configured_together() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="server", config="a2aserver.conf")
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    assert tuple((item.protocol.value, item.role.value) for item in agent.protocols) == (
        ("a2a", "server"),
        ("a2a", "client"),
    )


def test_client_operation_requires_configured_client_role() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    with pytest.raises(SecureAgentConfigurationError):
        asyncio.run(agent.send_message_to("https://provider.example", text="hello"))


def test_discovered_invocation_passes_registry_resource_to_platform_client() -> None:
    from agent_nebula_secureagent import DiscoveredAgent

    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")
    discovered = DiscoveredAgent(
        agent_id="inventory",
        display_name="Inventory",
        a2a_endpoint="https://provider.example/a2a",
        resource="https://provider.example",
    )

    result = asyncio.run(agent.send_message(
        discovered,
        data={"sku": "ABC"},
        skill_id="inventory.lookup",
    ))

    assert result == ({"message": "ok"},)
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "send"
    assert arguments["target"] == "https://provider.example/a2a"
    assert arguments["resource"] == "https://provider.example"
    assert arguments["skill_id"] == "inventory.lookup"


def test_discovery_requires_nebula_configuration() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    with pytest.raises(SecureAgentConfigurationError):
        asyncio.run(agent.discover(capability="inventory.lookup"))


def test_secureagent_close_is_noop_before_server_composition() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    asyncio.run(agent.close())
