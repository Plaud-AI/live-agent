"""
API Type Definitions

Provides common types and utilities for API interactions, including
connection options and sentinel values for optional parameters.
"""

from dataclasses import dataclass
from typing import Any, TypeVar, Union


# NOT_GIVEN Sentinel System
# =========================
# Used to distinguish between "parameter not provided" and "parameter explicitly set to None"

class _NotGiven:
    """
    Sentinel value for unset parameters.
    
    This allows distinguishing between:
    - Parameter not provided at all (NOT_GIVEN)
    - Parameter explicitly set to None (None)
    
    Example:
        def update(*, name: NotGivenOr[str] = NOT_GIVEN):
            if is_given(name):
                self.name = name  # Only update if explicitly provided
    """
    
    def __bool__(self) -> bool:
        return False
    
    def __repr__(self) -> str:
        return "NOT_GIVEN"


NOT_GIVEN = _NotGiven()
"""Sentinel value indicating a parameter was not provided"""

T = TypeVar("T")
NotGivenOr = Union[T, _NotGiven]
"""Type hint for optional parameters that can be NOT_GIVEN"""


def is_given(obj: Any) -> bool:
    """
    Check if a value was explicitly provided (not NOT_GIVEN).
    
    Args:
        obj: Value to check
    
    Returns:
        True if value was provided, False if NOT_GIVEN
    
    Example:
        >>> is_given("hello")
        True
        >>> is_given(None)
        True
        >>> is_given(NOT_GIVEN)
        False
    """
    return not isinstance(obj, _NotGiven)


# API Connection Options
# ======================

@dataclass
class APIConnectOptions:
    """
    Configuration options for API connections.
    
    Controls timeout, retry behavior, and other connection parameters.
    
    Attributes:
        timeout: Connection timeout in seconds
        max_retry: Maximum number of retry attempts on transient failures
        retry_interval: Initial delay between retries in seconds (may use exponential backoff)
        max_retry_interval: Maximum delay between retries in seconds
    
    Example:
        options = APIConnectOptions(
            timeout=30.0,
            max_retry=3,
            retry_interval=1.0,
        )
    """
    
    timeout: float = 10.0
    max_retry: int = 3
    retry_interval: float = 0.5
    max_retry_interval: float = 10.0
    
    def __post_init__(self) -> None:
        """Validate configuration values"""
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retry < 0:
            raise ValueError("max_retry must be non-negative")
        if self.retry_interval <= 0:
            raise ValueError("retry_interval must be positive")
        if self.max_retry_interval < self.retry_interval:
            raise ValueError("max_retry_interval must be >= retry_interval")


DEFAULT_API_CONNECT_OPTIONS = APIConnectOptions()
"""Default connection options used when none are specified"""

