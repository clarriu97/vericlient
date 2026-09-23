# API Documentation

The `vericlient` library provides a way to interact with the Veridas APIs.

To know how to configure the library, the following concepts must be understood:

- `target`: You can use the library to interact with the Veridas cloud APIs or with a
  self-hosted API. It will depend on the `url` parameter. If the `url` parameter
  is provided to the client object, the client will interact with the self-hosted
  API. Otherwise, it will interact with the Veridas cloud APIs.

- `url`: the URL of the API to interact with. If provided, the client will
  interact with this URL instead of the Veridas cloud APIs.

- `apikey`: the API key to use for the requests if the client is interacting
  with the Veridas Cloud API.

- `environment`: the environment to use for the requests if the client is
  interacting with the Veridas cloud APIs. It can be `production`
  or `sandbox`.

  Default: `sandbox`.

- `location`: the location to use for the requests if the client is interacting
  with the Veridas cloud APIs. It can be `eu` or `us`,
  depending if the server is located in Europe or the United States.

  Default: `eu`.

- `timeout`: the timeout for the requests in seconds.

  Default: `10`.

## Getting started

The entrypoint of the library will offer all the clients available to interact
with the Veridas APIs.
Example:

```python
from vericlient import DaspeakClient, VcspClient

daspeak_client = DaspeakClient()
vcsp_client = VcspClient()
```

## Configuration

The library can be configured both programmatically and using environment
variables.

### Programmatically

Simply pass the desired configuration parameters to the client constructor.

```python
from vericlient import DaspeakClient

client = DaspeakClient(
    apikey="your_api_key",
    environment="sandbox",
    location="eu",
    timeout=10,
)
```

Remember that there are some default values for the parameters, so you don't need
to provide all of them.

For example, if you want to use the sandbox European server, you can create the
client like this:

```python
from vericlient import DaspeakClient

client = DaspeakClient(apikey="your_api_key")
```

### Self-hosted deployments

Give the client a `url` and it skips the cloud entirely:

```python
from vericlient import DaspeakClient

client = DaspeakClient(url="https://veridas.internal.example.com/daspeak/v1")
```

Two things work differently from the cloud, both on purpose.

**The URL is used exactly as given**, service path included. For the cloud the client builds
it, because the environment and the location determine where the service lives. For a
self-hosted deployment only you know that, so nothing is appended.

**The `apikey` is ignored.** It is the Veridas cloud's authentication scheme, and a deployment
you run yourself has whatever you put in front of it instead. That is what `headers` is for:

```python
client = DaspeakClient(
    url="https://veridas.internal.example.com/daspeak/v1",
    headers={"Authorization": "Bearer your-token", "X-Tenant": "acme"},
)
```

Anything in `headers` is sent with every request. It is not limited to authentication, and it
is not limited to self-hosted deployments — a cloud client can carry its own headers too, for
tracing or routing, alongside the apikey:

```python
client = DaspeakClient(apikey="your_api_key", headers={"X-Request-Id": "abc123"})
```

### Environment variables

| Variable | Sets | Default |
|---|---|---|
| `VERICLIENT_APIKEY` | The API key used against the Veridas cloud | none |
| `VERICLIENT_ENVIRONMENT` | `sandbox` or `production` | `sandbox` |
| `VERICLIENT_LOCATION` | `eu` or `us` | `eu` |
| `VERICLIENT_URL` | A self-hosted URL, which replaces the cloud entirely | none |
| `VERICLIENT_TIMEOUT` | The request timeout in seconds | `10` |

### Precedence

Each setting is resolved in this order:

1. the argument passed to the client constructor,
2. the `VERICLIENT_` environment variable,
3. the library default.

```python
import os
from vericlient import DaspeakClient

os.environ["VERICLIENT_APIKEY"] = "from-the-environment"

DaspeakClient()  # uses "from-the-environment"
DaspeakClient(apikey="explicit")  # uses "explicit"
```

!!! warning "Changed in 0.2.0"

    Before 0.2.0 this was the other way round: an environment variable silently won over
    the constructor argument, so `DaspeakClient(apikey="explicit")` was ignored whenever
    `VERICLIENT_APIKEY` happened to be set, and two clients could not use two different
    keys in the same process.

Settings are read when a client is created, not when the library is imported, so changing
the environment between two constructor calls does what you would expect.
