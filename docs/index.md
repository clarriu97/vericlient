# Vericlient

[![CI](https://github.com/clarriu97/vericlient/actions/workflows/ci.yml/badge.svg)](https://github.com/clarriu97/vericlient/actions/workflows/ci.yml) [![Coverage](https://codecov.io/github/clarriu97/vericlient/branch/master/graph/badge.svg?token=H361XPC52E)](https://codecov.io/github/clarriu97/vericlient) [![PyPI](https://img.shields.io/pypi/v/vericlient?color=e92063)](https://pypi.org/project/vericlient/) [![Python versions](https://img.shields.io/pypi/pyversions/vericlient?color=e92063)](https://pypi.org/project/vericlient/) [![License: MIT](https://img.shields.io/badge/license-MIT-orange.svg)](https://opensource.org/licenses/MIT)

A Python client for the [Veridas APIs](https://docs.veridas.com/). It handles the request
plumbing, validates what goes in and out, and turns API errors into exceptions you can
actually catch, so integrating a Veridas service does not start with writing a client.

## Install

```bash
pip install vericlient
```

Python 3.11 or newer.

## Quickstart

Check that the service is reachable:

```python
from vericlient import DaspeakClient

client = DaspeakClient(apikey="your_api_key")
print(client.alive())
```

Enrol a voice and compare another recording against it:

```python
from vericlient import DaspeakClient
from vericlient.daspeak.models import CompareCredential2AudioInput, GenerateCredentialInput

client = DaspeakClient(apikey="your_api_key")

# A credential is the biometric representation of a voice. Generate one with the most
# recent model the service offers.
model = client.get_models().models[-1]
credential = client.generate_credential(
    GenerateCredentialInput(audio="/path/to/enrolment.wav", hash=model),
).credential

# Later, compare a new recording against it.
result = client.compare(
    CompareCredential2AudioInput(
        credential_reference=credential,
        audio_to_evaluate="/path/to/verification.wav",
    ),
)
print(f"Similarity: {result.score}")
```

Both `audio` and `audio_to_evaluate` accept a path or a `bytes` object, so nothing has to
touch the filesystem:

```python
with open("/path/to/enrolment.wav", "rb") as f:
    credential = client.generate_credential(
        GenerateCredentialInput(audio=f.read(), hash=model),
    ).credential
```

## Handling failures

Everything the client raises inherits from `VeriClientError`, and the specific exceptions
tell you what to fix:

```python
from vericlient.daspeak.exceptions import NetSpeechDurationIsNotEnoughError
from vericlient.exceptions import VeriClientError

try:
    client.generate_credential(GenerateCredentialInput(audio=recording, hash=model))
except NetSpeechDurationIsNotEnoughError as error:
    print(f"Ask for a longer recording: {error}")
except VeriClientError as error:
    print(f"Something else went wrong: {error}")
```

See [Error handling](errors.md) for the full list.

## Pointing somewhere else

By default the client talks to the European sandbox. Switch environment and location, or
give it a self-hosted URL and it will skip the cloud entirely:

```python
from vericlient import DaspeakClient

production = DaspeakClient(apikey="your_api_key", environment="production", location="us")
self_hosted = DaspeakClient(url="https://veridas.internal.example.com")
```

Every setting can also come from the environment. See
[Configuration](api_docs/vericlient.md#configuration).

## Where to next

- [Supported endpoints](supported_endpoints.md) — what is covered, per API
- [Configuration](api_docs/vericlient.md) — targets, environments and settings
- [Error handling](errors.md) — the exception tree
- [das-Peak usage](api_docs/daspeak/client_usage.md) and [VCSP usage](api_docs/vcsp/client_usage.md)
