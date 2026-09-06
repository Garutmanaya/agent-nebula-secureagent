"""Stable exceptions exposed by the SecureAgent developer API."""


class SecureAgentError(Exception):
    """Base exception for failures reported through the SecureAgent facade."""


class SecureAgentConfigurationError(SecureAgentError):
    """Raised when facade or protocol configuration is invalid."""


class SecureAgentSkillRegistrationError(SecureAgentError):
    """Raised when a business skill cannot be registered safely."""


class SecureAgentProtocolError(SecureAgentError):
    """Raised when a requested protocol capability is unavailable or invalid."""
