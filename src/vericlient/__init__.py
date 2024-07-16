"""vericlient module."""
from vericlient.daspeak.client import DaspeakClient
from vericlient.environments import Environments, Locations, Target

__all__ = [
    "DaspeakClient",
    "Locations",
    "Environments",
    "Target",
]
