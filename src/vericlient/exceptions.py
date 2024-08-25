"""General exceptions for the VeriClient package."""
from requests.models import Response


class VeriClientError(Exception):
    """Base class for exceptions in the VeriClient package."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class ServerError(VeriClientError):
    """Exception raised for server errors."""

    def __init__(self, response: Response) -> None:
        message = f"The server encountered an error with status code {response.status_code}: {response}"
        super().__init__(message)


class AuthorizationError(VeriClientError):
    """Exception raised for authorization errors."""

    def __init__(self) -> None:
        message = "The request was not authorized. Did you provide the correct API key?"
        super().__init__(message)


class UnsupportedMediaTypeError(VeriClientError):
    """Exception raised for unsupported media type errors."""

    def __init__(self) -> None:
        message = "The media type of the request is not supported."
        super().__init__(message)


class InvalidCredentialError(VeriClientError):
    """Exception raised for invalid credentials."""

    def __init__(self) -> None:
        message = "The credential/s provided are invalid."
        super().__init__(message)
