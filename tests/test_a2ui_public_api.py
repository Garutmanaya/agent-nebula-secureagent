"""Public A2UI facade tests."""

from agent_nebula_secureagent import create_memory_a2ui_session_service
from agent_nebula_secureagent.a2ui import A2UIProtocolPolicy, A2UISessionService


def test_memory_a2ui_session_service_is_public_secureagent_api() -> None:
    service = create_memory_a2ui_session_service()
    assert isinstance(service, A2UISessionService)


def test_a2ui_validation_policy_is_available_through_secureagent() -> None:
    policy = A2UIProtocolPolicy(
        supported_versions=("v1.0",),
        preferred_version="v1.0",
        allowed_catalog_ids=("catalog:test",),
    )
    assert policy.preferred_version == "v1.0"
