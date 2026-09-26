"""Public logging facade for SecureAgent applications.

Applications consume the common Agent Nebula UTC console format through this
module instead of importing Platform implementation modules directly.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from agent_nebula_platform.observability.logging import (
    DATE_FORMAT,
    LOG_FORMAT,
    UTCFormatter,
    configure_console_logger,
    create_utc_formatter,
)
from agent_nebula_platform.platform.configuration import PlatformApplicationConfigurationLoader


@dataclass(frozen=True, slots=True)
class SecureAgentLoggingConfiguration:
    """Console logging settings declared by ``secureagent.conf``."""

    console_logging: bool = True
    log_level: str = "INFO"


def load_logging_configuration(
    config: str | Path = "secureagent.conf",
) -> SecureAgentLoggingConfiguration:
    """Load public logging settings from SecureAgent application configuration."""

    application = PlatformApplicationConfigurationLoader().load(Path(config))
    return SecureAgentLoggingConfiguration(
        console_logging=application.console_logging,
        log_level=application.log_level,
    )


def create_uvicorn_log_config(
    config: SecureAgentLoggingConfiguration,
    *,
    application_loggers: Iterable[str] = (),
) -> dict[str, object] | None:
    """Build Uvicorn logging config using the standard Agent Nebula UTC format.

    ``None`` intentionally delegates to Uvicorn when console logging is disabled;
    callers should also pass ``access_log=False`` in that case.
    """

    if not config.console_logging:
        return None

    loggers: dict[str, object] = {
        "uvicorn": {
            "handlers": ["default"],
            "level": config.log_level,
            "propagate": False,
        },
        "uvicorn.error": {"level": config.log_level},
        "uvicorn.access": {
            "handlers": ["access"],
            "level": config.log_level,
            "propagate": False,
        },
    }
    for logger_name in dict.fromkeys(application_loggers):
        normalized = logger_name.strip()
        if normalized:
            loggers[normalized] = {
                "handlers": ["default"],
                "level": config.log_level,
                "propagate": False,
            }

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "nebula": {
                "()": UTCFormatter,
                "format": LOG_FORMAT,
                "datefmt": DATE_FORMAT,
            },
        },
        "handlers": {
            "default": {
                "formatter": "nebula",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
            },
            "access": {
                "formatter": "nebula",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": loggers,
    }


__all__ = [
    "DATE_FORMAT",
    "LOG_FORMAT",
    "SecureAgentLoggingConfiguration",
    "UTCFormatter",
    "configure_console_logger",
    "create_utc_formatter",
    "create_uvicorn_log_config",
    "load_logging_configuration",
]
