"""
Implementation of the client for the DASPEaK service.
"""
from requests.models import Response as Response
from vericlient.client import Client
from vericlient.daspeak.endpoints import Endpoints


class DaspeakClient(Client):
    """
    Class to interact with the Daspeak API
    """
    def __init__(
            self,
            api: str = None,
            apikey: str = None,
            target: str = None,
            timeout: int = None,
            environment: str = None,
            location: str = None,
            url: str = None,
            headers: dict = None,
    ) -> None:
        """
        Constructor for the DaspeakClient class
        """
        super().__init__(
            api=api,
            apikey=apikey,
            target=target,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )

    def alive(self) -> bool:
        """
        Method to check if the service is alive
        """
        response = self._get(endpoint=Endpoints.ALIVE.value)
        return response.status_code == 200

    def _handle_error_response(self, response: Response):
        pass
