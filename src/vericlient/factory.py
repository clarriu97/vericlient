"""
Factory module for creating VeriClient instances.
"""
from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.daspeak.client import DasPeakClient


class VericlientFactory:
    """
    The VericlientFactory class is responsible for creating client instances.
    """
    def get_client(client_type: str, *args, **kwargs) -> Client:
        """
        Method to create a client instance for the specified API.
        """
        if client_type not in APIs:
            raise ValueError(f"Invalid client type: {client_type}. Valid options are: {', '.join(APIs)}.")
        if client_type == APIs.DASPEAK:
            return DasPeakClient(*args, **kwargs)
