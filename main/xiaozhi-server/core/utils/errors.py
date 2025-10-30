"""
API Error Classes

Provides a hierarchy of exception classes for API-related errors,
offering better error classification and handling than standard Python exceptions.
"""

from typing import Any


class APIError(Exception):
    """
    Base class for all API-related errors.
    
    This is the parent class for all API exceptions. Catching this exception
    will catch all API-related errors.
    """
    
    def __init__(self, message: str, **kwargs: Any) -> None:
        super().__init__(message)
        self.message = message
        self.details = kwargs


class APIConnectionError(APIError):
    """
    Connection to API failed.
    
    Raised when unable to establish a connection to the API endpoint.
    This could be due to network issues, DNS resolution failures, etc.
    
    Example:
        raise APIConnectionError("Failed to connect to Cartesia API", host="api.cartesia.ai")
    """
    pass


class APITimeoutError(APIError):
    """
    API request timed out.
    
    Raised when an API request exceeds the configured timeout duration.
    
    Example:
        raise APITimeoutError("Request timed out after 30s", timeout=30)
    """
    
    def __init__(self, message: str, *, timeout: float | None = None, **kwargs: Any) -> None:
        super().__init__(message, timeout=timeout, **kwargs)
        self.timeout = timeout


class APIStatusError(APIError):
    """
    API returned an error status code.
    
    Raised when the API returns a non-2xx HTTP status code or an error response.
    
    Example:
        raise APIStatusError(
            "Invalid API key",
            status_code=401,
            response_body='{"error": "unauthorized"}'
        )
    """
    
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        response_body: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, status_code=status_code, response_body=response_body, **kwargs)
        self.status_code = status_code
        self.response_body = response_body
    
    def __str__(self) -> str:
        base_msg = self.message
        if self.status_code:
            base_msg = f"[{self.status_code}] {base_msg}"
        if self.response_body:
            base_msg = f"{base_msg}\nResponse: {self.response_body[:200]}"
        return base_msg


class APIAuthenticationError(APIStatusError):
    """
    Authentication failed.
    
    Raised when API key is invalid, expired, or missing required permissions.
    
    Example:
        raise APIAuthenticationError("Invalid API key", status_code=401)
    """
    pass


class APIRateLimitError(APIStatusError):
    """
    Rate limit exceeded.
    
    Raised when the API rate limit has been exceeded.
    
    Example:
        raise APIRateLimitError("Rate limit exceeded", status_code=429, retry_after=60)
    """
    
    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after

