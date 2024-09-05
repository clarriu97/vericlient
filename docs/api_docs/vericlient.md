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
from vericlient import DaspeakClient, DasfaceClient

daspeak_client = DaspeakClient()
dasface_client = DasfaceClient()
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

### Environment variables

The following environment variables are supported and will override the
programmatic configuration:

- `VERICLIENT_ENVIRONMENT`: The environment to use for the requests.
- `VERICLIENT_APIKEY`: The API key to use for the requests against the Veridas Cloud API.
- `VERICLIENT_LOCATION`: The location to use for the requests.
- `VERICLIENT_URL`: In case you want to use a self-hosted API, you can set the URL with this variable.
- `VERICLIENT_TIMEOUT`: The timeout for the requests.
