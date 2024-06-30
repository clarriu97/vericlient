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
    Environments.SANDBOX: {
        Locations.EU: f"https://api-work.{Locations.EU}.veri-das.com",
        Locations.US: f"https://api-work.{Locations.US}.veri-das.com",
    },
    Environments.PRODUCTION: {
        Locations.EU: f"https://api.{Locations.EU}.veri-das.com",
        Locations.US: f"https://api.{Locations.US}.veri-das.com",
    },
}
