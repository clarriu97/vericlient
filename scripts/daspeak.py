"""
Example script to demonstrate how to use the daspeak module.
"""
from vericlient import VericlientFactory, APIs

client = VericlientFactory.get_client(api=APIs.DASPEAK, apikey="your_api_key")

print(client.alive())
