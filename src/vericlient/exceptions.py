"""General exceptions for the VeriClient package."""
from requests.models import Response


class ServerError(Exception):
    """Exception raised for server errors"""
    def __init__(self, response: Response) -> None:
        message = f"The server encountered an error with status code {response.status_code}: {response}"
        super().__init__(message)
