"""Public SecureAgent A2UI client/runtime facade.

Applications import A2UI runtime types from SecureAgent rather than depending on
Agent Nebula Platform directly. Platform remains the implementation owner; this
module freezes the application-facing names needed by generic A2UI clients such
as Agent Explorer and orchestrators.
"""

from __future__ import annotations

from agent_nebula_platform.a2ui import (
    A2UIActionDispatcher,
    A2UIActionRecord,
    A2UIComponentPolicy,
    A2UIMessage,
    A2UIProtocolPolicy,
    A2UISessionService,
    A2UISessionSnapshot,
    A2UISurface,
    A2UISurfaceFrame,
    A2UISurfaceMode,
    A2UITaskReference,
    MemoryA2UISessionStore,
)
from agent_nebula_platform.platform.events import NullEventSink


def create_memory_a2ui_session_service() -> A2UISessionService:
    """Create an in-memory A2UI session service through the SecureAgent API."""

    return A2UISessionService(
        store=MemoryA2UISessionStore(),
        events=NullEventSink(),
    )


__all__ = [
    "A2UIActionDispatcher",
    "A2UIActionRecord",
    "A2UIComponentPolicy",
    "A2UIMessage",
    "A2UIProtocolPolicy",
    "A2UISessionService",
    "A2UISessionSnapshot",
    "A2UISurface",
    "A2UISurfaceFrame",
    "A2UISurfaceMode",
    "A2UITaskReference",
    "create_memory_a2ui_session_service",
]
