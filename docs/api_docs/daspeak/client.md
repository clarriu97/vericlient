# Daspeak Client

This is an example of how to use the
[Daspeak](https://docs.veridas.com/das-peak/cloud/latest/) client:

```python
from io import BytesIO

from vericlient import DaspeakClient
from vericlient.daspeak.models import (
    ModelsHashCredentialAudioInput,
    CompareCredential2AudioInput,
    CompareAudio2AudioInput,
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
model_output = client.generate_credential(model_input)
print(f"Credential generated with an audio file: {model_output.credential}")

# generate a credential from a BytesIO object using the last model
with open("/home/audio.wav", "rb") as f:
    model_input = ModelsHashCredentialAudioInput(
        audio=BytesIO(f.read()),
        hash=client.get_models().models[-1],
    )
model_output = client.generate_credential(model_input)
print(f"Credential generated with virtual file: {model_output.credential}")

# compare a credential with an audio file
similarity_input = CompareCredential2AudioInput(
    audio_to_evaluate="/home/audio.wav",
    credential_reference=model_output.credential,
)
similarity_output = client.compare(similarity_input)
print(f"Similarity between the credential and the audio file: {similarity_output.score}")
print(f"Authenticity of the audio file: {similarity_output.authenticity_to_evaluate}")
print(f"Net speech duration of the audio file: {similarity_output.net_speech_duration_to_evaluate}")

# compare a credential with a BytesIO object
with open("/home/audio.wav", "rb") as f:
    similarity_input = CompareCredential2AudioInput(
        audio_to_evaluate=BytesIO(f.read()),
        credential_reference=model_output.credential,
    )
similarity_output = client.compare(similarity_input)
print(f"Similarity between the credential and the virtual file: {similarity_output.score}")
print(f"Authenticity of the virtual file: {similarity_output.authenticity_to_evaluate}")
print(f"Net speech duration of the virtual file: {similarity_output.net_speech_duration_to_evaluate}")

# compare two audio files, no matter if they are virtual or real
with open ("/home/audio.wav", "rb") as f:
    similarity_input = CompareAudio2AudioInput(
        audio_reference="/home/audio.wav",
        audio_to_evaluate=BytesIO(f.read()),
    )
similarity_output = client.compare(similarity_input)
print(f"Similarity between the two audio files: {similarity_output.score}")
print(f"Authenticity of the audio file reference: {similarity_output.authenticity_reference}")
print(f"Authenticity of the audio file to evaluate: {similarity_output.authenticity_to_evaluate}")
```

::: vericlient.daspeak.client.DaspeakClient
