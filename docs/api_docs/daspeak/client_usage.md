# Daspeak Client usage

This is an example of how to use the
[Daspeak](https://docs.veridas.com/das-peak/cloud/latest/) client:

## Check if the API is alive

```python
from vericlient import DaspeakClient

client = DaspeakClient(apikey="your_api_key")
print(f"Alive: {client.alive()}")
```

## Get the available biometrics models

```python
from vericlient import DaspeakClient

client = DaspeakClient(apikey="your_api_key")
print(f"Biometrics models: {client.get_models().models}")
```

## Generate a credential from an audio file

The following code generates a credential from an audio file using the last model:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import GenerateCredentialInput

client = DaspeakClient(apikey="your_api_key")
model_input = GenerateCredentialInput(
    audio="/home/audio.wav",
    hash=client.get_models().models[-1],
)
generate_credential_output = client.generate_credential(model_input)
print(f"Credential generated with an audio file: {generate_credential_output.credential}")
```

You can also check the authenticity of the audio file, its duration, and its net speech duration:

```python
print(f"Authenticity of the audio file: {generate_credential_output.authenticity}")
print(f"Duration of the audio file: {generate_credential_output.duration}")
print(f"Net speech duration of the audio file: {generate_credential_output.net_speech_duration}")
```

## Generate a credential from a BytesIO object

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import GenerateCredentialInput

client = DaspeakClient(apikey="your_api_key")
with open("/home/audio.wav", "rb") as f:
    model_input = GenerateCredentialInput(
        audio=f.read(),
        hash=client.get_models().models[-1],
    )
generate_credential_output = client.generate_credential(model_input)
print(f"Credential generated with virtual file: {generate_credential_output.credential}")
```

## Compare a credential with an audio file

You can compare a credential with an audio file using the following code:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareCredential2AudioInput

client = DaspeakClient(apikey="your_api_key")
compare_input = CompareCredential2AudioInput(
    audio_to_evaluate="/home/audio.wav",
    credential_reference=generate_credential_output.credential,
)
compare_output = client.compare(compare_input)
print(f"Similarity between the credential and the audio file: {compare_output.score}")
```

Similarly, you can check the authenticity of the audio file and its durations durations:

```python
print(f"Authenticity of the audio file: {compare_output.authenticity_to_evaluate}")
print(f"Durations of the audio file: {compare_output.duration_to_evaluate}")
print(f"Net speech duration of the audio file: {compare_output.net_speech_duration_to_evaluate}")
```

## Compare a credential with a BytesIO object

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareCredential2AudioInput

client = DaspeakClient(apikey="your_api_key")
with open("/home/audio.wav", "rb") as f:
    compare_input = CompareCredential2AudioInput(
        audio_to_evaluate=f.read(),
        credential_reference=generate_credential_output.credential,
    )
compare_output = client.compare(compare_input)
print(f"Similarity between the credential and the virtual file: {compare_output.score}")
```

## Compare two audio files

You can compare two audio files, no matter if they are virtual or real:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareAudio2AudioInput

client = DaspeakClient(apikey="your_api_key")
with open ("/home/audio.wav", "rb") as f:
    compare_input = CompareAudio2AudioInput(
        audio_reference="/home/audio.wav",
        audio_to_evaluate=f.read(),
    )
compare_output = client.compare(compare_input)
print(f"Similarity between the two audio files: {compare_output.score}")
```

## Compare two credentials

You can compare two credentials using the following code:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareCredential2CredentialInput

client = DaspeakClient(apikey="your_api_key")
compare_input = CompareCredential2CredentialInput(
    credential_reference=generate_credential_output.credential,
    credential_to_evaluate=generate_credential_output.credential,
)
compare_output = client.compare(compare_input)
print(f"Similarity between the two credentials: {compare_output.score}")
```

## Identify a subject comparing an audio against a list of credentials

You can identify a subject comparing an audio against a list of credentials using the following code:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareAudio2CredentialsInput

client = DaspeakClient(apikey="your_api_key")
compare_input = CompareAudio2CredentialsInput(
    audio_reference="/home/audio.wav",
    credential_list=[
        ("subject1_credential", generate_credential_output.credential),
        ("subject2_credential", generate_credential_output.credential),   
    ],
)
compare_output = client.compare(compare_input)
print(f"Subject identified: {compare_output.scores}")
```
