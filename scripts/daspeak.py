"""
Example script to demonstrate how to use the daspeak module.
"""
from vericlient import VericlientFactory, APIs

client = VericlientFactory.get_client(APIs.DASPEAK.value, apikey="your_api_key")

print(client.alive())
print(client.get_models())
