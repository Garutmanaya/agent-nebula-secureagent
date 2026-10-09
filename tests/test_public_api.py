from pathlib import Path

import pytest

from agent_nebula_secureagent import SecureAgent
from agent_nebula_secureagent.exceptions import (
    SecureAgentConfigurationError,
    SecureAgentSkillRegistrationError,
)


def test_secureagent_default_configuration_filename() -> None:
    agent = SecureAgent()
    assert agent._application_config == Path("secureagent.conf")


def test_secureagent_accepts_user_selected_configuration_filename(tmp_path: Path) -> None:
    config = tmp_path / "my-agent.conf"
    agent = SecureAgent(config=config)
    assert agent._application_config == config





def test_llm_observability_is_public() -> None:
    """SecureAgent exposes Platform-neutral LLM usage observability types."""
    from agent_nebula_secureagent import LlmCostEstimator, LlmUsageObserver, LlmUsageRecord

    assert LlmCostEstimator is not None
    assert LlmUsageObserver is not None
    assert LlmUsageRecord is not None

