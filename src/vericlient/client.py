"""Module with the abstraction of the client to interact with the Veridas APIs"""
import requests
from abc import ABC, abstractmethod

import structlog

from vericlient.environments import Environments, Locations, Target, cloud_env2url
from vericlient.config.config import settings
from vericlient.apis import APIs
from vericlient.exceptions import ServerError


logger = structlog.get_logger(__name__)


class Client(ABC):
    """
    Class to interact with the Veridas APIs
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
        Constructor for the Client class
        """
        self._headers = headers or {}
        self._session = requests.Session()

        if not target and not settings.target:
            logger.warning("No target provided. Defaulting to cloud")
            self._target = Target.CLOUD.value
        else:
            self._target = settings.target or target
        if not any(self._target == target.value for target in Target):
            raise ValueError(f"Invalid target: {target}. Valid options are: {', '.join(target.value for target in Target)}")

        if not timeout and not settings.timeout:
            seconds = 10
            logger.warning(f"No timeout provided. Defaulting to {seconds} seconds")
            self._timeout = seconds
        else:
            self._timeout = settings.timeout or timeout

        if self._target == Target.CLOUD.value:
            self._configure_cloud_url(api, environment, location)
            if not apikey and not settings.apikey:
                raise ValueError("If target is cloud, apikey must be provided")
            apikey = settings.apikey or apikey
            self._headers.update({"apikey": apikey})
        elif self._target == Target.CUSTOM:
            self._configure_custom_url(url)

        self._session.headers.update(self._headers)

    def _configure_cloud_url(self, api: str, environment: str, location: str):
        if not environment and not settings.environment:
            logger.warning("No environment provided. Defaulting to sandbox")
            environment = Environments.SANDBOX.value
        else:
            environment = settings.environment or environment
        if not any(environment == env.value for env in Environments):
            raise ValueError(f"Invalid environment: {environment}. Valid options are: {', '.join(env.value for env in Environments)}")

        if not location and not settings.location:
            logger.warning("No location provided. Defaulting to EU")
            location = Locations.EU.value
        else:
            location = settings.location or location
        if not any(location == loc.value for loc in Locations):
            raise ValueError(f"Invalid location: {location}. Valid options are: {', '.join(loc.value for loc in Locations)}")

        if not any(api == api_.value for api_ in APIs):
            raise ValueError(f"If target is cloud, valid api must be provided. Valid options are: {', '.join(api.value for api in APIs)}")
        self._url = cloud_env2url[environment][location] + f"/{api}"

    def _configure_custom_url(self, url: str):
        if not url and not settings.url:
            raise ValueError("If target is custom, url must be provided")
        self._url = url
 
    @property
    def url(self):
        return self._url

    @property
    def headers(self):
        return self._headers

    @property
    def timeout(self):
        return self._timeout

    @abstractmethod
    def alive(self) -> bool:
        """
        Method to check if the API is alive and responding.
        """

    @abstractmethod
    def _handle_error_response(self, response: requests.Response):
        """
        Method to handle error responses from the API.
        """

    def _get(self, endpoint: str) -> requests.Response:
        """
        Method to make a GET request to the API.
        """
        response = self._session.get(f"{self._url}/{endpoint}", timeout=self._timeout)
        if not response.ok:
            self._handle_error_response(response)
        return response

    def _post(self, endpoint: str, data: dict = None, json_: dict = None, files: dict = None) -> requests.Response:
        """
        Method to make a POST request to the API.
        """
        response = self._session.post(
            f"{self._url}/{endpoint}",
            data=data,
            json=json_,
            files=files,
            timeout=self._timeout,
        )
        if not response.ok:
            self._handle_error_response(response)
        return response

    def _raise_server_error(self, response: requests.Response):
        """
        Method to raise a ServerError exception.
        """
        raise ServerError(response)
