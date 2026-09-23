<h1 align="center">vericlient</h1>

<p align="center">
  <em>A Python client for the Veridas APIs — voice and face biometrics, without writing the plumbing.</em>
</p>

<p align="center">
  <a href="https://github.com/clarriu97/vericlient/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/clarriu97/vericlient/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://codecov.io/github/clarriu97/vericlient"><img alt="Coverage" src="https://codecov.io/github/clarriu97/vericlient/branch/master/graph/badge.svg?token=H361XPC52E"></a>
  <a href="https://pypi.org/project/vericlient/"><img alt="PyPI" src="https://img.shields.io/pypi/v/vericlient?color=e92063"></a>
  <a href="https://pypi.org/project/vericlient/"><img alt="Python versions" src="https://img.shields.io/pypi/pyversions/vericlient?color=e92063"></a>
  <a href="https://vericlient.larri.dev/"><img alt="Documentation" src="https://img.shields.io/badge/docs-vericlient.larri.dev-e92063"></a>
  <a href="https://opensource.org/licenses/MIT"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-orange.svg"></a>
</p>

<p align="center">
  <a href="https://vericlient.larri.dev/">Documentation</a> ·
  <a href="https://vericlient.larri.dev/supported_endpoints/">Supported endpoints</a> ·
  <a href="https://vericlient.larri.dev/errors/">Error handling</a> ·
  <a href="https://vericlient.larri.dev/CHANGELOG/">Changelog</a>
</p>

---

[Veridas](https://docs.veridas.com/) exposes its biometrics products as HTTP APIs, and every
integration starts by writing the same client: multipart uploads, per-service error codes,
environment and region routing. `vericlient` is that client, so you can get to the part that
is actually yours.

- **Typed in and out.** Every request and response is a pydantic model, so a malformed call
  fails where you made it, not three layers down.
- **Errors you can catch.** API failures arrive as specific exceptions —
  `NetSpeechDurationIsNotEnoughError`, not a 400 and a string to parse.
- **Cloud or self-hosted.** Sandbox and production, EU and US, or your own deployment.
- **Three runtime dependencies**, all of them ones you probably already have.

## API support

| API | Status | Coverage |
|---|:--:|---|
| [das-Peak](https://docs.veridas.com/das-peak/cloud/latest) — voice biometrics | 🟢 | 11 / 11 endpoints |
| [VCSP](https://docs.veridas.com/vcsp_echo/cloud/latest) — managed credential storage | 🟢 | 31 / 31 endpoints |
| [das-Face](https://docs.veridas.com/das-face/cloud/latest) — face biometrics | 🟢 | 11 / 11 endpoints, plus the 2 liveness challenge ones |

Endpoint by endpoint in [Supported endpoints](https://vericlient.larri.dev/supported_endpoints/).

## Install

```bash
pip install vericlient
```

Python 3.11 or newer.

## Quickstart

```python
from vericlient import DaspeakClient

client = DaspeakClient(apikey="your_api_key")

# A credential is the biometric representation of a voice.
model = client.get_models().models[-1]
credential = client.generate_credential(audio="/path/to/enrolment.wav", hash=model).credential

# Compare a new recording against it.
result = client.compare_credential_to_audio(
    credential_reference=credential,
    audio_to_evaluate="/path/to/verification.wav",
)
print(f"Similarity: {result.score}")
```

Audio can be a path or a `bytes` object, so nothing has to touch the filesystem.

Point the client somewhere else with `environment`, `location`, or a `url` for a self-hosted
deployment:

```python
DaspeakClient(apikey="your_api_key", environment="production", location="us")
DaspeakClient(url="https://veridas.internal.example.com")
```

## Configuration

Every setting can be passed to the constructor or read from an environment variable. The
constructor argument wins, the environment fills in what you left out, and the library falls
back to its own default.

| Variable | Sets | Default |
|---|---|---|
| `VERICLIENT_APIKEY` | The API key used against the Veridas cloud | none |
| `VERICLIENT_ENVIRONMENT` | `sandbox` or `production` | `sandbox` |
| `VERICLIENT_LOCATION` | `eu` or `us` | `eu` |
| `VERICLIENT_URL` | A self-hosted URL, which replaces the cloud entirely | none |
| `VERICLIENT_TIMEOUT` | The request timeout in seconds | `10` |

## Runnable examples

One script per client in [`scripts/`](scripts), each covering every endpoint that client
supports. They run as they stand — they default to the repository's own test media — so with
an API key in the environment:

```bash
VERICLIENT_APIKEY=your_api_key pdm run python scripts/daspeak.py
```

The VCSP one creates an account, a group and two tags, and removes all of them before it
ends. Run it against a sandbox.

## Contributing

Issues and pull requests are welcome. The project uses [PDM](https://pdm-project.org):

```bash
pdm install --dev
pdm run lint && pdm run format-check && pdm run test
```

Tests run against mocks by default. To exercise a real environment, set `VERICLIENT_APIKEY`
and run `SERVICE=daspeak pdm run test-eu-sandbox`.

## Licence

[MIT](LICENSE).
