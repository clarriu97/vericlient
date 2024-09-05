"""Environments that the client can make requests to."""

from enum import Enum


class Environments(Enum):
    """Represents the environments that the client can make requests to, if the target is the cloud."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


class Locations(Enum):
    """Represents the locations that the client can make requests to, if the target is the cloud."""

    EU = "eu"
    US = "us"


cloud_env2url = {
    Environments.SANDBOX.value: {
        Locations.EU.value: f"https://api-work.{Locations.EU.value}.veri-das.com",
        Locations.US.value: f"https://api-work.{Locations.US.value}.veri-das.com",
    },
    Environments.PRODUCTION.value: {
        Locations.EU.value: f"https://api.{Locations.EU.value}.veri-das.com",
        Locations.US.value: f"https://api.{Locations.US.value}.veri-das.com",
    },
}
