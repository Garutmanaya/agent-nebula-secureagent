"""Public SecureAgent logging facade tests."""

from pathlib import Path

from agent_nebula_secureagent import (
    SecureAgentLoggingConfiguration,
    create_uvicorn_log_config,
    load_logging_configuration,
)
from agent_nebula_secureagent.logging import DATE_FORMAT, LOG_FORMAT, UTCFormatter


def test_load_logging_configuration_reads_secureagent_runtime_settings(tmp_path: Path) -> None:
    config = tmp_path / "secureagent.conf"
    config.write_text(
        "[runtime.application]\n"
        "name = explorer\n"
        f"product_root = {tmp_path}\n"
        f"runtime_root = {tmp_path}\n"
        "console_logging = true\n"
        "log_level = WARNING\n",
        encoding="utf-8",
    )

    settings = load_logging_configuration(config)

    assert settings == SecureAgentLoggingConfiguration(
        console_logging=True,
        log_level="WARNING",
    )


def test_uvicorn_log_config_uses_standard_utc_formatter() -> None:
    result = create_uvicorn_log_config(
        SecureAgentLoggingConfiguration(log_level="INFO"),
        application_loggers=("agent_explorer",),
    )

    assert result is not None
    formatter = result["formatters"]["nebula"]
    assert formatter["()"] is UTCFormatter
    assert formatter["format"] == LOG_FORMAT
    assert formatter["datefmt"] == DATE_FORMAT
    assert result["loggers"]["agent_explorer"]["level"] == "INFO"


def test_uvicorn_log_config_is_disabled_with_console_logging() -> None:
    result = create_uvicorn_log_config(
        SecureAgentLoggingConfiguration(console_logging=False)
    )
    assert result is None


def test_secureagent_exposes_its_logging_configuration(tmp_path: Path) -> None:
    from agent_nebula_secureagent import SecureAgent

    config = tmp_path / "secureagent.conf"
    config.write_text(
        "[runtime.application]\n"
        "name = explorer\n"
        f"product_root = {tmp_path}\n"
        f"runtime_root = {tmp_path}\n"
        "console_logging = false\n"
        "log_level = ERROR\n",
        encoding="utf-8",
    )

    assert SecureAgent(config).logging == SecureAgentLoggingConfiguration(
        console_logging=False,
        log_level="ERROR",
    )
