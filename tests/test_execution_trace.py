"""Public SecureAgent execution-trace facade contracts."""

import pytest

from agent_nebula_platform.platform.execution_trace import record_execution_event
from agent_nebula_secureagent import execution_trace


def test_execution_trace_forwards_sanitized_platform_events() -> None:
    """SecureAgent should expose sanitized Platform events without leaking internals."""

    observed: list[dict] = []
    with execution_trace("ex_test", recorder=observed.append):
        record_execution_event(
            {
                "type": "TOKEN_RESPONSE",
                "details": {"access_token": "secret", "scope": "demo.read"},
            }
        )

    assert observed == [
        {
            "type": "TOKEN_RESPONSE",
            "details": {"access_token": "<redacted>", "scope": "demo.read"},
        }
    ]


def test_execution_trace_rejects_blank_execution_id() -> None:
    """A host must provide a usable correlation identifier."""

    with pytest.raises(ValueError, match="execution_id must not be blank"):
        with execution_trace("   ", recorder=lambda event: None):
            pass


def test_execution_trace_restores_previous_context_after_exception() -> None:
    """A failed operation must not leak its recorder into later work."""

    observed: list[dict] = []
    with pytest.raises(RuntimeError, match="boom"):
        with execution_trace("ex_failed", recorder=observed.append):
            record_execution_event({"type": "BEFORE_FAILURE"})
            raise RuntimeError("boom")

    record_execution_event({"type": "AFTER_FAILURE"})
    assert observed == [{"type": "BEFORE_FAILURE"}]
