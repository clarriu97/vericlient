"""Example script to demonstrate how to use the Vcsp module.
"""
from vericlient import VcspClient
from vericlient.vcsp.models import AssuranceMethodInput


client = VcspClient(apikey="your_api_key")

# check if the server is alive
print()
print(f"Alive: {client.alive()}")

# get all credential configurations
print()
print(f"Credential configurations: {client.get_credential_configurations()}")

# get all assurance methods
print()
assurance_methods = client.get_assurance_methods()
print(f"Assurance methods: {assurance_methods.assurance_methods}")

# get an assurance method
all_assurance_methods = []
for assurance_method in assurance_methods.assurance_methods:
    assurance_method_data = client.get_assurance_method(
        data_model=AssuranceMethodInput(urn=assurance_method)
    )
    all_assurance_methods.append(assurance_method_data)

print()
print(f"Each assurance method individually: {all_assurance_methods}")
