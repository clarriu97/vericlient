"""Module with the abstraction of the client to interact with the Veridas APIs."""

from abc import ABC, abstractmethod
from typing import TypeVar

import requests
import structlog

from vericlient.apis import APIs
from vericlient.config import DEFAULT_TIMEOUT, Settings
from vericlient.environments import Environments, Locations, cloud_env2url
from vericlient.exceptions import AuthorizationError, ServerError

logger = structlog.get_logger(__name__)

T = TypeVar("T")


def _first(*values: T | None) -> T | None:
    """Return the first value that is not None.

    This is the precedence rule the whole client follows: what the caller passed wins over
    the environment, which wins over the built-in default.
    """
    return next((value for value in values if value is not None), None)


class Client(ABC):
    """Class to interact with the Veridas APIs."""

    def __init__(
        self,
        api: APIs,
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
        settings = Settings()

        self._timeout = _first(timeout, settings.timeout, DEFAULT_TIMEOUT)

        url = _first(url, settings.url)
        if url:
            self._url = url
        else:
            self._configure_cloud_url(
                api,
                _first(environment, settings.environment),
                _first(location, settings.location),
            )
            apikey = _first(apikey, settings.apikey)
            if not apikey:
                error = "If target is cloud, apikey must be provided"
                raise ValueError(error)
            self._headers.update({"apikey": apikey})

        self._session.headers.update(self._headers)

    def _configure_cloud_url(self, api: APIs, environment: str | None, location: str | None) -> None:
        if not environment:
            logger.warning("No environment provided. Defaulting to sandbox")
            environment = Environments.SANDBOX.value
        if not any(environment == env.value for env in Environments):
            error = f"Invalid environment: {environment}. Valid options are: {', '.join(env.value for env in Environments)}"
            raise ValueError(error)

        if not location:
            logger.warning("No location provided. Defaulting to EU")
            location = Locations.EU.value
        if not any(location == loc.value for loc in Locations):
            error = f"Invalid location: {location}. Valid options are: {', '.join(loc.value for loc in Locations)}"
            raise ValueError(error)

        if not isinstance(api, APIs):
            valid = ", ".join(api_.api_name for api_ in APIs)
            error = f"If target is cloud, api must be one of the APIs enum members: {valid}"
            raise TypeError(error)
        self._url = cloud_env2url[environment][location] + f"/{api.path}"

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

    def _get(self, endpoint: str, params: dict | None = None) -> requests.Response:
        """Make a GET request to the API."""
        response = self._session.get(f"{self._url}/{endpoint}", params=params, timeout=self._timeout)
        if not response.ok:
            self._handle_authorization_error(response)
            self._handle_error_response(response)
        return response

    def _post(
        self,
        endpoint: str,
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

    def _delete(self, endpoint: str, json_: dict | None = None) -> requests.Response:
        """Make a DELETE request to the API."""
        response = self._session.delete(f"{self._url}/{endpoint}", json=json_, timeout=self._timeout)
        if not response.ok:
            self._handle_authorization_error(response)
            self._handle_error_response(response)
        return response

    def _raise_server_error(self, response: requests.Response) -> None:
        """Raise a ServerError exception."""
        raise ServerError(response)

    def _error_payload(self, response: requests.Response) -> dict:
        """Return the body of a failed response as JSON.

        Error bodies are not always JSON. A gateway in front of the API answers a 502 with
        an HTML page, and the decode error that used to escape from here said nothing about
        what had actually gone wrong.

        Raises:
            ServerError: If the body cannot be decoded as a JSON object

        """
        try:
            payload = response.json()
        except ValueError as error:
            raise ServerError(response) from error
        if not isinstance(payload, dict):
            raise ServerError(response)
        return payload

    def _handle_authorization_error(self, response: requests.Response) -> None:
        """Raise AuthorizationError when the server rejected the credentials.

        A rejected request does not always answer with JSON: a gateway can reply with an
        HTML error page, in which case there is nothing to inspect and the caller falls
        through to the API-specific handler.
        """
        try:
            payload = response.json()
        except ValueError:
            return
        if not isinstance(payload, dict):
            return
        message = payload.get("message")
        if isinstance(message, str) and "no Authorization header found" in message:
            raise AuthorizationError
