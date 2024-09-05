"""vericlient module."""
from vericlient.daspeak.client import DaspeakClient
from vericlient.environments import Environments, Locations

__all__ = [
    "DaspeakClient",
    "Locations",
    "Environments",
]
