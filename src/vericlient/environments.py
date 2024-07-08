"""Environments that the client can make requests to."""

from enum import Enum


class Target(Enum):
    CLOUD = "cloud"
    CUSTOM = "custom"


class Environments(Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class Locations(Enum):
    EU = "eu"
    US = "us"


cloud_env2url = {
    Environments.SANDBOX.value: {
        Locations.EU.value: f"https://api-work.{Locations.EU.value}.veri-das.com",
        Locations.US.value: f"https://api-work.{Locations.US.value}.veri-das.com",
    },
    Environments.PRODUCTION: {
        Locations.EU.value: f"https://api.{Locations.EU.value}.veri-das.com",
        Locations.US.value: f"https://api.{Locations.US.value}.veri-das.com",
    },
}
