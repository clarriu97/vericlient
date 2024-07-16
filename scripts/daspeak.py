"""Example script to demonstrate how to use the daspeak module.
"""
from io import BytesIO

from vericlient import DaspeakClient
from vericlient.daspeak.models import ModelsHashCredentialWavInput

client = DaspeakClient(apikey="your_api_key")

# check if the server is alive
print(f"Alive: {client.alive()}")

# get the available biometrics models
print(f"Biometrics models: {client.get_models().models}")

# generate a credential from an audio file using the last model
model_input = ModelsHashCredentialWavInput(
    audio="/home/audio.wav",
    hash=client.get_models().models[-1],
)
model_output = client.generate_credential(model_input)
print(f"Credential generated with an audio file: {model_output.credential}")

# generate a credential from a BytesIO object using the last model
with open("/home/audio.wav", "rb") as f:
    model_input = ModelsHashCredentialWavInput(
        audio=BytesIO(f.read()),
        hash=client.get_models().models[-1],
    )
model_output = client.generate_credential(model_input)
print(f"Credential generated with virtual file: {model_output.credential}")
