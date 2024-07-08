"""
Factory module for creating VeriClient instances.
"""
from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.daspeak.client import DaspeakClient


class VericlientFactory:
    """
    The VericlientFactory class is responsible for creating client instances.
    """
    def get_client(self, client_type: str, *args, **kwargs) -> Client:
        """
        Method to create a client instance for the specified API.
        """
        
        if not any(client_type == api.value for api in APIs):
            raise ValueError(f"Invalid client type: {client_type}. Valid options are: {', '.join(api.value for api in APIs)}")
        if client_type == APIs.DASPEAK.value:
            return DaspeakClient(client_type, *args, **kwargs)
