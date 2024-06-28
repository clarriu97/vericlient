"""
Factory module for creating VeriClient instances.
"""
from vericlient.apis import APIs
from vericlient.client import Client


class VericlientFactory:
    """
    
    """
    def get_client(
        client_type: str,
        api_key: str = None,
        environment: str = "production",
        timeout: int = 10
    ) -> Client:
        """
        Method to create a client instance for the specified API.
        """
