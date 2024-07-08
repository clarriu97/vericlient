"""
Implementation of the client for the DASPEaK service.
"""
import requests

from requests.models import Response as Response

from vericlient.client import Client
from vericlient.daspeak.endpoints import DaspeakEndpoints
from vericlient.daspeak.models import (
    ModelsOutput
)


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
        response = self._get(endpoint=DaspeakEndpoints.ALIVE.value)
        return response.status_code == 200

    def _handle_error_response(self, response: Response):
        pass

    def get_models(self) -> ModelsOutput:
        """
        Get the models available biometrics models in the service.
        """
        response = self._get(endpoint=DaspeakEndpoints.MODELS.value)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._handle_error_response(response)
        return ModelsOutput(**response.json())
