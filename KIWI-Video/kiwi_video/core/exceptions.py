"""Custom exceptions for KIWI-Video framework."""


class KiwiVideoError(Exception):
    """Base exception for all KIWI-Video errors."""

    pass


class AgentError(KiwiVideoError):
    """Exception raised for agent-related errors."""

    def __init__(self, agent_name: str, message: str) -> None:
        self.agent_name = agent_name
        self.message = message
        super().__init__(f"[{agent_name}] {message}")


class ProviderError(KiwiVideoError):
    """Exception raised for provider-related errors."""

    def __init__(self, provider_name: str, message: str) -> None:
        self.provider_name = provider_name
        self.message = message
        super().__init__(f"[{provider_name}] {message}")


class StateError(KiwiVideoError):
    """Exception raised for state management errors."""

    pass


class ConfigurationError(KiwiVideoError):
    """Exception raised for configuration errors."""

    pass


class ValidationError(KiwiVideoError):
    """Exception raised for validation errors."""

    pass


class ResourceNotFoundError(KiwiVideoError):
    """Exception raised when a required resource is not found."""

    def __init__(self, resource_type: str, resource_id: str) -> None:
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} not found: {resource_id}")


class TimeoutError(KiwiVideoError):
    """Exception raised when an operation times out."""

    pass


class MaxRetriesExceededError(KiwiVideoError):
    """Exception raised when maximum retries are exceeded."""

    def __init__(self, operation: str, max_retries: int) -> None:
        self.operation = operation
        self.max_retries = max_retries
        super().__init__(f"Max retries ({max_retries}) exceeded for operation: {operation}")

