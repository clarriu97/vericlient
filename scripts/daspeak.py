"""Example script to demonstrate how to use the daspeak module.
"""
from io import BytesIO

from vericlient import DaspeakClient
from vericlient.daspeak.models import (
    ModelsHashCredentialAudioInput,
    CompareCredential2AudioInput,
    CompareAudio2AudioInput,
    CompareCredential2CredentialInput
)

client = DaspeakClient(apikey="your_api_key")

# check if the server is alive
print(f"Alive: {client.alive()}")

# get the available biometrics models
print(f"Biometrics models: {client.get_models().models}")

# generate a credential from an audio file using the last model
model_input = ModelsHashCredentialAudioInput(
    audio="/home/audio.wav",
    hash=client.get_models().models[-1],
)
generate_credential_output = client.generate_credential(model_input)
print(f"Credential generated with an audio file: {generate_credential_output.credential}")

# generate a credential from a BytesIO object using the last model
with open("/home/audio.wav", "rb") as f:
    model_input = ModelsHashCredentialAudioInput(
        audio=BytesIO(f.read()),
        hash=client.get_models().models[-1],
    )
generate_credential_output = client.generate_credential(model_input)
print(f"Credential generated with virtual file: {generate_credential_output.credential}")

# compare a credential with an audio file
compare_input = CompareCredential2AudioInput(
    audio_to_evaluate="/home/audio.wav",
    credential_reference=generate_credential_output.credential,
)
compare_output = client.compare(compare_input)
print(f"Similarity between the credential and the audio file: {compare_output.score}")
print(f"Authenticity of the audio file: {compare_output.authenticity_to_evaluate}")
print(f"Net speech duration of the audio file: {compare_output.net_speech_duration_to_evaluate}")

# compare a credential with a BytesIO object
with open("/home/audio.wav", "rb") as f:
    compare_input = CompareCredential2AudioInput(
        audio_to_evaluate=BytesIO(f.read()),
        credential_reference=generate_credential_output.credential,
    )
compare_output = client.compare(compare_input)
print(f"Similarity between the credential and the virtual file: {compare_output.score}")
print(f"Authenticity of the virtual file: {compare_output.authenticity_to_evaluate}")
print(f"Net speech duration of the virtual file: {compare_output.net_speech_duration_to_evaluate}")

# compare two audio files, no matter if they are virtual or real
with open ("/home/audio.wav", "rb") as f:
    compare_input = CompareAudio2AudioInput(
        audio_reference="/home/audio.wav",
        audio_to_evaluate=BytesIO(f.read()),
    )
compare_output = client.compare(compare_input)
print(f"Similarity between the two audio files: {compare_output.score}")
print(f"Authenticity of the audio file reference: {compare_output.authenticity_reference}")
print(f"Authenticity of the audio file to evaluate: {compare_output.authenticity_to_evaluate}")

# compare two credentials
compare_input = CompareCredential2CredentialInput(
    credential_reference=generate_credential_output.credential,
    credential_to_evaluate=generate_credential_output.credential,
)
compare_output = client.compare(compare_input)
print(f"Similarity between the two credentials: {compare_output.score}")

