"""Module to define the endpoints for Daspeak API"""
from enum import Enum

from vericlient.endpoints import Endpoints


class DaspeakEndpoints(Enum):
    alive = Endpoints.ALIVE.value
