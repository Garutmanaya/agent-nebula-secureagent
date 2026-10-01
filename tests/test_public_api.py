from pathlib import Path

import asyncio

import pytest

from agent_nebula_secureagent import ProtocolType, SecureAgent
from agent_nebula_secureagent.exceptions import (
    SecureAgentConfigurationError,
    SecureAgentProtocolError,
    SecureAgentSkillRegistrationError,
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
        from types import SimpleNamespace

        type(self).calls.append(("resolve", dict(kwargs)))
        return SimpleNamespace(name="remote-agent")

    async def connect(self, **kwargs):
        from types import SimpleNamespace

        type(self).calls.append(("connect", dict(kwargs)))
        return SimpleNamespace(close=lambda: None)

    async def send_message(self, **kwargs):
        type(self).calls.append(("send", dict(kwargs)))
        return ({"message": "ok"},)

    async def send_a2ui_action(self, **kwargs):
        """Record one protocol-neutral A2UI action delegation."""
        type(self).calls.append(("a2ui_action", dict(kwargs)))
        return ({"message": "a2ui-ok"},)


def _client_registry():
    from agent_nebula_secureagent.protocols import ProtocolAdapterRegistry

    _RecordingClientAdapter.calls = []
    return ProtocolAdapterRegistry(client_adapters=(_RecordingClientAdapter(),))


def test_secureagent_resolves_agent_card_through_configured_client() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    card = asyncio.run(agent.resolve_agent_card("https://provider.example"))

    assert card.name == "remote-agent"
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "resolve"
    assert arguments["protocol_config"] == Path("a2aclient.conf")
    assert arguments["target"] == "https://provider.example"


def test_secureagent_exposes_configured_native_a2a_client() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    client = asyncio.run(agent.a2a_client("https://provider.example"))

    assert client is not None
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "connect"
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


def test_discovered_invocation_uses_agent_card_security_independent_of_registry_resource() -> None:
    from agent_nebula_secureagent import DiscoveredAgent

    agent = SecureAgent(protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")
    discovered = DiscoveredAgent(
        agent_id="inventory",
        display_name="Inventory",
        agent_card_url="https://provider.example/.well-known/agent-card.json",
        # Registry projections are informational and must not become invocation authority.
        a2a_endpoint="https://registry.example/stale-a2a-endpoint",
    )

    result = asyncio.run(agent.send_message(
        discovered,
        data={"sku": "ABC"},
        skill_id="inventory.lookup",
    ))

    assert result == ({"message": "ok"},)
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "send"
    assert arguments["target"] == "https://provider.example/.well-known/agent-card.json"
    assert "resource" not in arguments
    assert arguments["skill_id"] == "inventory.lookup"


def test_discovery_requires_nebula_configuration() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    with pytest.raises(SecureAgentConfigurationError):
        asyncio.run(agent.discover(capability="inventory.lookup"))


def test_secureagent_close_is_noop_before_server_composition() -> None:
    agent = SecureAgent(protocol_registry=_client_registry())
    asyncio.run(agent.close())


def test_a2a_executable_skill_preserves_complete_skill_result() -> None:
    """SecureAgent must not discard metadata or A2UI before Platform mapping."""
    from agent_nebula_platform.skills import SkillResult
    from agent_nebula_secureagent.protocols.a2a import _A2AExecutableSkill

    agent = SecureAgent()
    expected = SkillResult(data={"value": 1}, metadata={"source": "test"})

    @agent.skill("result.complete")
    def complete(_payload):
        return expected

    executable = _A2AExecutableSkill(agent.skills[0])
    result = asyncio.run(executable.handler({"input": True}))

    assert result is expected
    assert result.metadata == {"source": "test"}


def test_secureagent_passes_independent_a2ui_config_to_server_adapter() -> None:
    """The facade passes the A2UI path without parsing protocol configuration."""
    class RecordingServerAdapter:
        protocol = ProtocolType.A2A
        arguments: dict[str, object] = {}

        def compose(self, **kwargs):
            type(self).arguments = dict(kwargs)
            return object()

    from agent_nebula_secureagent.protocols import ProtocolAdapterRegistry

    adapter = RecordingServerAdapter()
    agent = SecureAgent(
        a2ui_config="a2ui.conf",
        protocol_registry=ProtocolAdapterRegistry(server_adapters=(adapter,)),
    )
    agent.use_protocol("a2a", role="server", config="a2aserver.conf")

    @agent.skill("general.hello")
    def hello(payload):
        return payload

    agent.compose()

    assert adapter.arguments["protocol_config"] == Path("a2aserver.conf")
    assert adapter.arguments["a2ui_config"] == Path("a2ui.conf")


def test_secureagent_passes_independent_a2ui_config_to_client_adapter() -> None:
    """Outbound A2UI intent crosses the facade as configuration, not A2A metadata."""
    agent = SecureAgent(
        a2ui_config="a2ui.conf",
        protocol_registry=_client_registry(),
    )
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    asyncio.run(agent.send_message_to("https://provider.example", text="hello"))

    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "send"
    assert arguments["a2ui_config"] == Path("a2ui.conf")


def test_secureagent_sends_a2ui_action_response_options_through_configured_client() -> None:
    """A2UI response options must propagate without undefined adapter state."""
    agent = SecureAgent(a2ui_config="a2ui.conf", protocol_registry=_client_registry())
    agent.use_protocol("a2a", role="client", config="a2aclient.conf")

    result = asyncio.run(
        agent.send_a2ui_action(
            "https://provider.example",
            name="parking.space.hold",
            surface_id="parking-1",
            source_component_id="space-1",
            context={"spaceId": "L1-A-01"},
            want_response=True,
            action_id="action-1",
        )
    )

    assert result == ({"message": "a2ui-ok"},)
    operation, arguments = _RecordingClientAdapter.calls[-1]
    assert operation == "a2ui_action"
    assert arguments["want_response"] is True
    assert arguments["action_id"] == "action-1"


def test_skill_preserves_structured_contract_metadata() -> None:
    agent = SecureAgent("schema-test")
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object", "properties": {"airport": {"type": "string"}}, "required": ["airport"]}

    @agent.skill("parking.search", schema_contract_id="https://agentnebula.ai/contracts/parking/search/v1", input_schema=schema)
    def search(payload):
        return payload

    skill = agent.skills[0]
    assert skill.schema_contract_id == "https://agentnebula.ai/contracts/parking/search/v1"
    assert skill.input_schema == schema
    assert skill.output_schema is None


def test_skill_schema_requires_contract_id() -> None:
    agent = SecureAgent("schema-test")
    with pytest.raises(SecureAgentSkillRegistrationError, match="requires schema_contract_id"):
        agent.skill("parking.search", input_schema={"type": "object"})


def test_secureagent_passes_a2ui_action_handler_to_server_adapter() -> None:
    """Server composition preserves the application-owned A2UI action callback."""
    class RecordingServerAdapter:
        protocol = ProtocolType.A2A
        arguments: dict[str, object] = {}

        def compose(self, **kwargs):
            type(self).arguments = dict(kwargs)
            return object()

    from agent_nebula_secureagent.protocols import ProtocolAdapterRegistry

    async def handle_action(action, payload):
        return {"handled": action.name, "payload": dict(payload)}

    adapter = RecordingServerAdapter()
    agent = SecureAgent(
        a2ui_config="a2ui.conf",
        protocol_registry=ProtocolAdapterRegistry(server_adapters=(adapter,)),
    )
    agent.use_protocol("a2a", role="server", config="a2aserver.conf")
    agent.set_a2ui_action_handler(handle_action)

    @agent.skill("general.hello")
    def hello(payload):
        return payload

    agent.compose()

    assert adapter.arguments["a2ui_action_handler"] is handle_action


def test_a2a_adapter_passes_a2ui_action_handler_to_platform(monkeypatch) -> None:
    """A2A adapter forwards the application callback without interpreting events."""
    agent = SecureAgent()

    @agent.skill("general.hello")
    def hello(payload):
        return payload

    async def handle_action(action, payload):
        return {"handled": action.name}

    monkeypatch.setattr(
        "agent_nebula_secureagent.protocols.a2a.A2AStandaloneApplicationComposer",
        _RecordingA2AComposer,
    )
    A2AServerProtocolAdapter().compose(
        application_config=Path("secureagent.conf"),
        protocol_config=Path("a2aserver.conf"),
        nebula_config=None,
        skills=agent.skills,
        a2ui_action_handler=handle_action,
    )

    assert _RecordingA2AComposer.arguments["a2ui_action_handler"] is handle_action


def test_a2ui_presentation_facade_uses_secureagent_configuration(tmp_path) -> None:
    """Provider presentation composition stays behind the SecureAgent facade."""
    a2ui_config = tmp_path / "a2ui.conf"
    a2ui_config.write_text(
        "[a2ui]\n"
        "enabled = true\n"
        "version = v1.0\n"
        "supported_catalog_ids = https://example.test/catalog.json\n"
        "default_catalog_id = https://example.test/catalog.json\n"
        "accepts_inline_catalogs = false\n",
        encoding="utf-8",
    )
    presentation_path = tmp_path / "presentation.json"
    presentation_path.write_text(
        '{"components":[{"id":"root","component":"Text","text":"Hello"}],"dataModel":{"value":"initial"}}',
        encoding="utf-8",
    )
    agent = SecureAgent(a2ui_config=a2ui_config)

    presentation = agent.load_a2ui_presentation(presentation_path)
    surface = agent.create_a2ui_surface(presentation, surface_id="surface-1")
    update = agent.update_a2ui_surface("surface-1", data_model={"value": "updated"})

    create_document = surface.messages[0].document
    assert create_document["createSurface"]["catalogId"] == "https://example.test/catalog.json"
    assert create_document["createSurface"]["dataModel"] == {"value": "initial"}
    assert update.messages[0].document["updateDataModel"]["value"] == {"value": "updated"}


def test_llm_observability_is_public() -> None:
    """SecureAgent exposes Platform-neutral LLM usage observability types."""

    from agent_nebula_secureagent import LlmCostEstimator, LlmUsageObserver, LlmUsageRecord

    assert LlmCostEstimator is not None
    assert LlmUsageObserver is not None
    assert LlmUsageRecord is not None
