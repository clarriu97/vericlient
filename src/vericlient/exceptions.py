"""General exceptions for the VeriClient package."""
from requests.models import Response


class ServerError(Exception):
    """Exception raised for server errors."""

    def __init__(self, response: Response) -> None:
        message = f"The server encountered an error with status code {response.status_code}: {response}"
        super().__init__(message)


class AuthorizationError(Exception):
    """Exception raised for authorization errors."""

    def __init__(self) -> None:
        message = "The request was not authorized. Did you provide the correct API key?"
        super().__init__(message)
