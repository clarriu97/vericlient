"""Module with the abstraction of the client to interact with the Veridas APIs."""
from abc import ABC, abstractmethod

import requests
import structlog

from vericlient.apis import APIs
from vericlient.config.config import settings
from vericlient.environments import Environments, Locations, cloud_env2url
from vericlient.exceptions import AuthorizationError, ServerError

logger = structlog.get_logger(__name__)


class Client(ABC):
    """Class to interact with the Veridas APIs."""

    def __init__(
            self,
            api: str,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create Client class."""
        self._headers = headers or {}
        self._session = requests.Session()

        if not timeout and not settings.timeout:
            seconds = 10
            logging_message = f"No timeout provided. Defaulting to {seconds} seconds"
            logger.warning(logging_message)
            self._timeout = seconds
        else:
            self._timeout = settings.timeout or timeout

        if url:
            self._configure_custom_url(url)
        else:
            self._configure_cloud_url(api, environment, location)
            if not apikey and not settings.apikey:
                error = "If target is cloud, apikey must be provided"
                raise ValueError(error)
            apikey = settings.apikey or apikey
            self._headers.update({"apikey": apikey})

        self._session.headers.update(self._headers)

    def _configure_cloud_url(self, api: str, environment: str, location: str) -> None:
        if not environment and not settings.environment:
            logger.warning("No environment provided. Defaulting to sandbox")
            environment = Environments.SANDBOX.value
        else:
            environment = settings.environment or environment
        if not any(environment == env.value for env in Environments):
            error = f"Invalid environment: {environment}. Valid options are: {', '.join(env.value for env in Environments)}"
            raise ValueError(error)

        if not location and not settings.location:
            logger.warning("No location provided. Defaulting to EU")
            location = Locations.EU.value
        else:
            location = settings.location or location
        if not any(location == loc.value for loc in Locations):
            error = f"Invalid location: {location}. Valid options are: {', '.join(loc.value for loc in Locations)}"
            raise ValueError(error)

        if not any(api == api_.value for api_ in APIs):
            error = f"If target is cloud, valid api must be provided. Valid options are: {', '.join(api.value for api in APIs)}"
            raise ValueError(error)
        self._url = cloud_env2url[environment][location] + f"/{api}"

    def _configure_custom_url(self, url: str) -> None:
        url = settings.url or url
        self._url = url

    @property
    def url(self) -> str:
        """Return the URL of the API."""
        return self._url

    @property
    def headers(self) -> dict:
        """Return the headers of the API."""
        return self._headers

    @property
    def timeout(self) -> int:
        """Return the timeout of the API."""
        return self._timeout

    @abstractmethod
    def alive(self) -> bool:
        """Check if the API is alive and responding."""

    @abstractmethod
    def _handle_error_response(self, response: requests.Response) -> None:
        """Handle error responses from the API."""

    def _get(self, endpoint: str) -> requests.Response:
        """Make a GET request to the API."""
        response = self._session.get(f"{self._url}/{endpoint}", timeout=self._timeout)
        if not response.ok:
            self._handle_authorization_error(response)
            self._handle_error_response(response)
        return response

    def _post(
            self, endpoint: str,
            data: dict | None = None,
            json_: dict | None = None,
            files: dict | None = None,
    ) -> requests.Response:
        """Make a POST request to the API."""
        response = self._session.post(
            f"{self._url}/{endpoint}",
            data=data,
            json=json_,
            files=files,
            timeout=self._timeout,
        )
        if not response.ok:
            self._handle_authorization_error(response)
            self._handle_error_response(response)
        return response

    def _raise_server_error(self, response: requests.Response) -> None:
        """Raise a ServerError exception."""
        raise ServerError(response)

    def _handle_authorization_error(self, response: requests.Response) -> None:
        """Handle authorization errors."""
        try:
            message = response.json()["message"]
            if "no Authorization header found" in message:
                raise AuthorizationError
        except KeyError:
            pass
