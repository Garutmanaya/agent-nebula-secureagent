from pathlib import Path

import pytest

from agent_nebula_secureagent import ProtocolType, SecureAgent
from agent_nebula_secureagent.exceptions import (
    SecureAgentConfigurationError,
    SecureAgentProtocolError,
)




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
