# Welcome

[![License: MIT](https://img.shields.io/badge/License-MIT-orange.svg)](https://opensource.org/licenses/MIT) [![Documentation](https://img.shields.io/badge/docs-GitHub%20Pages-blue)](https://clarriu97.github.io/vericlient/) [![CI](https://github.com/clarriu97/vericlient/actions/workflows/ci.yml/badge.svg)](https://github.com/clarriu97/vericlient/actions/workflows/ci.yml) [![codecov](https://codecov.io/github/clarriu97/vericlient/branch/master/graph/badge.svg?token=H361XPC52E)](https://codecov.io/github/clarriu97/vericlient) [![PyPI version](https://badge.fury.io/py/vericlient.svg)](https://badge.fury.io/py/vericlient) [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/clarriu97/vericlient/graphs/commit-activity)

Vericlient is a Python library designed to facilitate interaction with
the [Veridas API](https://docs.veridas.com/).
It provides a simple and robust interface for making API requests and
handling responses efficiently.

# Features

- **Easy to Use**: Designed to be intuitive and easy to integrate into your projects.
- **Exception Handling**: Includes error and exception handling for safer interaction with the API.
- **Modular and Extensible**: Structured to easily add new functionalities and endpoints.
- **Minimal Dependencies** to work.

# APIs support

- 🟢: fully supported. 
- 🟠: partly supported.
- 🔴: not yet supported.

| **API**  | **Supported** |
|----------|:-------------:|
| das-Peak |       🟠      |
| VCSP     |       🔴      |

# Installation

To install the library, you can use pip:

```bash
pip install vericlient
```

# Usage

To use the library, you need to import the `VericlientFactory` class and
create an instance of it.
Then, ask the factory to create a client for the desired API and get the
client instance.
Finally, use the client to make requests to the API.

```python
from io import BytesIO

from vericlient import DaspeakClient
from vericlient.daspeak.models import (
    ModelsHashCredentialAudioInput,
    CompareCredential2AudioInput
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
similarity_output = client.similarity_credential2audio(similarity_input)
print(f"Similarity between the credential and the audio file: {similarity_output.score}")
print(f"Authenticity of the audio file: {similarity_output.authenticity_to_evaluate}")
print(f"Net speech duration of the audio file: {similarity_output.net_speech_duration_to_evaluate}")

# compare a credential with a BytesIO object
with open("/home/audio.wav", "rb") as f:
    similarity_input = CompareCredential2AudioInput(
        audio_to_evaluate=BytesIO(f.read()),
        credential_reference=model_output.credential,
    )
similarity_output = client.similarity_credential2audio(similarity_input)
print(f"Similarity between the credential and the virtual file: {similarity_output.score}")
print(f"Authenticity of the virtual file: {similarity_output.authenticity_to_evaluate}")
print(f"Net speech duration of the virtual file: {similarity_output.net_speech_duration_to_evaluate}")
```

You can also use the client against any self-hosted Veridas API:

```python
from vericlient import DaspeakClient

# Create a client for the das-Peak API
client = DaspeakClient(url="https://your-self-hosted-api.com")

# Test the connection
print(client.alive())
```

# Configuration

The library can be configured using environment variables.
The following variables are supported:

- `VERICLIENT_TARGET`: The target API to use (default: `cloud`).
- `VERICLIENT_ENVIRONMENT`: The environment to use for the requests (default: `production`).
- `VERICLIENT_APIKEY`: The API key to use for the requests against the Veridas Cloud API.
- `VERICLIENT_LOCATION`: The location to use for the requests (default: `eu`).
- `VERICLIENT_URL`: In case you want to use a self-hosted API, you can set the URL with this variable.
- `VERICLIENT_TIMEOUT`: The timeout for the requests (default: `10`).
