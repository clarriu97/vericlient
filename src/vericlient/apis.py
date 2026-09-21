"""Module to define the APIs that can be used from Veridas."""

from enum import Enum


class APIs(Enum):
    """Enum with the available APIs and the version each one is served under.

    Veridas versions every API independently: das-Peak and VCSP are served under `v1`,
    das-Face under `v2`. Name and version are kept apart so a client can name its API
    without hardcoding the path it happens to live at today.
    """

    DASPEAK = ("daspeak", "v1")
    VCSP = ("vcsp", "v1")

    def __init__(self, api_name: str, version: str) -> None:
        self.api_name = api_name
        self.version = version

    @property
    def path(self) -> str:
        """Return the path the API is served under, such as `daspeak/v1`."""
        return f"{self.api_name}/{self.version}"
