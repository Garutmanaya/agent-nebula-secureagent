from pathlib import Path

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
