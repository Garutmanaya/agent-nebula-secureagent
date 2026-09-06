"""Stable developer-facing Agent Nebula discovery models."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class DiscoveredSkill:
    """One skill advertised by a provider returned from Agent Nebula discovery."""

    skill_id: str
    name: str | None = None
    description: str | None = None
    required_scopes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DiscoveredAgent:
    """Protocol-neutral discovery result with secure A2A invocation metadata."""

    agent_id: str
    display_name: str
    external_agent_id: str | None = None
    provider_id: str | None = None
    provider_name: str | None = None
    category: str | None = None
    tags: tuple[str, ...] = ()
    trust_status: str | None = None
    lifecycle_status: str | None = None
    resource: str | None = None
    agent_card_url: str | None = None
    a2a_endpoint: str | None = None
    protocols: tuple[str, ...] = ()
    skills: tuple[DiscoveredSkill, ...] = ()
    raw_document: Mapping[str, Any] = field(default_factory=dict)

    @property
    def invokable(self) -> bool:
        """Return whether discovery supplied the metadata required for A2A invocation."""
        return bool(self.resource and self.a2a_endpoint)

    def require_a2a_invocation(self) -> tuple[str, str]:
        """Return A2A endpoint and OAuth resource, failing closed when incomplete."""
        if not self.a2a_endpoint or not self.resource:
            raise ValueError(
                "Discovered agent does not expose both A2A endpoint and protected-resource metadata"
            )
        return self.a2a_endpoint, self.resource


class DiscoveryNormalizer:
    """Normalize Registry response envelopes without coupling to one API revision."""

    def normalize(self, payload: Mapping[str, Any] | Sequence[Any]) -> tuple[DiscoveredAgent, ...]:
        return tuple(
            agent
            for record in self._records(payload)
            if (agent := self._agent(record)) is not None
        )

    @staticmethod
    def _records(payload: Mapping[str, Any] | Sequence[Any]) -> tuple[Mapping[str, Any], ...]:
        if isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            return tuple(item for item in payload if isinstance(item, Mapping))
        if not isinstance(payload, Mapping):
            return ()
        for key in ("items", "agents", "results"):
            values = payload.get(key)
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
                return tuple(item for item in values if isinstance(item, Mapping))
        return (payload,) if any(key in payload for key in ("agent_id", "id", "external_agent_id")) else ()

    @classmethod
    def _agent(cls, record: Mapping[str, Any]) -> DiscoveredAgent | None:
        document = cls._document(record)
        endpoints = cls._first_mapping(record.get("endpoints"), document.get("endpoints"))
        protected = cls._first_mapping(
            record.get("protected_resource"),
            record.get("protected_resource_metadata"),
            document.get("protected_resource"),
        )
        provider = cls._mapping(record.get("provider"))
        agent_id = cls._first_string(record.get("agent_id"), record.get("id"), record.get("external_agent_id"), document.get("id"))
        if agent_id is None:
            return None
        a2a_endpoint = cls._first_string(record.get("a2a_endpoint"), endpoints.get("a2a"), document.get("url"))
        resource = cls._first_string(
            record.get("resource_identifier"), record.get("resource"), protected.get("resource"), record.get("base_url")
        )
        if resource is None and a2a_endpoint:
            resource = a2a_endpoint.rstrip("/").removesuffix("/a2a")
        categories = cls._strings(record.get("categories"))
        return DiscoveredAgent(
            agent_id=agent_id,
            display_name=cls._first_string(record.get("display_name"), record.get("name"), document.get("name")) or agent_id,
            external_agent_id=cls._first_string(record.get("external_agent_id"), document.get("id")),
            provider_id=cls._first_string(record.get("provider_id"), provider.get("provider_id"), provider.get("id")),
            provider_name=cls._first_string(record.get("provider_name"), provider.get("display_name"), provider.get("name")),
            category=cls._first_string(record.get("category"), document.get("category")) or (categories[0] if categories else None),
            tags=cls._strings(record.get("tags") or document.get("tags")),
            trust_status=cls._first_string(record.get("trust_status"), record.get("trust")),
            lifecycle_status=cls._first_string(record.get("lifecycle_status"), record.get("status")),
            resource=resource,
            agent_card_url=cls._first_string(record.get("agent_card_url"), record.get("agent_card_uri"), endpoints.get("agent_card"), document.get("agent_card_url")),
            a2a_endpoint=a2a_endpoint,
            protocols=cls._strings(record.get("protocols") or document.get("protocols")),
            skills=cls._skills(record, document),
            raw_document=dict(record),
        )

    @classmethod
    def _skills(cls, record: Mapping[str, Any], document: Mapping[str, Any]) -> tuple[DiscoveredSkill, ...]:
        values = document.get("skills") or record.get("skills")
        if not isinstance(values, Sequence) or isinstance(values, (str, bytes, bytearray)):
            return ()
        result: list[DiscoveredSkill] = []
        for value in values:
            if not isinstance(value, Mapping):
                continue
            skill_id = cls._first_string(value.get("skill_id"), value.get("id"))
            if skill_id:
                result.append(DiscoveredSkill(
                    skill_id=skill_id,
                    name=cls._first_string(value.get("name")),
                    description=cls._first_string(value.get("description")),
                    required_scopes=cls._strings(value.get("required_scopes")),
                ))
        return tuple(result)

    @classmethod
    def _document(cls, record: Mapping[str, Any]) -> Mapping[str, Any]:
        return cls._first_mapping(
            record.get("discovery_document"), record.get("agent_card_document"),
            record.get("agent_card"), record.get("document"), record.get("card")
        )

    @staticmethod
    def _mapping(value: Any) -> Mapping[str, Any]:
        return value if isinstance(value, Mapping) else {}

    @classmethod
    def _first_mapping(cls, *values: Any) -> Mapping[str, Any]:
        for value in values:
            mapped = cls._mapping(value)
            if mapped:
                return mapped
        return {}

    @staticmethod
    def _first_string(*values: Any) -> str | None:
        for value in values:
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    @staticmethod
    def _strings(value: Any) -> tuple[str, ...]:
        if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
            return ()
        return tuple(dict.fromkeys(item.strip() for item in value if isinstance(item, str) and item.strip()))
