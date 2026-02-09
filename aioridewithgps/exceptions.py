"""Exceptions for the aioridewithgps library.

These exceptions provide a clear hierarchy for handling different types
of errors that can occur when communicating with the Ride with GPS API.
"""


class RideWithGPSError(Exception):
    """Base exception for all Ride with GPS errors.

    All other exceptions in this library inherit from this class,
    so you can catch this to handle any RWGPS-related error.
    """


class AuthenticationError(RideWithGPSError):
    """Raised when authentication fails.

    This happens when the API key is invalid, the auth token has expired,
    or the email/password combination is incorrect during login.
    """


class NotFoundError(RideWithGPSError):
    """Raised when a requested resource is not found (HTTP 404).

    For example, requesting a trip or route by an ID that doesn't exist.
    """


class ForbiddenError(RideWithGPSError):
    """Raised when access to a resource is forbidden (HTTP 403).

    The user is authenticated but doesn't have permission to access
    the requested resource (e.g., another user's private route).
    """


class ApiError(RideWithGPSError):
    """Raised for general API errors (HTTP 4xx/5xx) not covered above.

    Stores the HTTP status code and error message for debugging.
    """

    def __init__(self, status: int, message: str) -> None:
        """Initialize with the HTTP status code and error message."""
        self.status = status
        self.message = message
        super().__init__(f"API error {status}: {message}")
