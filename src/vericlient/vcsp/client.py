"""Implementation of the client for the VCSP service."""
from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.vcsp.endpoints import VcspEndpoints


class VcspClient(Client):
    """Class to interact with the VCSP API."""

    def __init__(
            self,
            api: str = APIs.VCSP.value,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the VcspClient class.

        Args:
            api: The API to use
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        super().__init__(
            api=api,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        self._exceptions = [
        ]

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=VcspEndpoints.ALIVE.value)
        accepted_status_code = 204
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API."""
