"""Example script to demonstrate how to use the Vcsp module.
"""
from vericlient import VcspClient


client = VcspClient(apikey="your_api_key")

# check if the server is alive
print(f"Alive: {client.alive()}")
