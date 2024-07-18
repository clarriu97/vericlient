# API Documentation

The `vericlient` library provides a way to interact with the Veridas APIs.

To know how to configure the library, the following concepts must be understood:

- `target`: the target of the client, which can be `cloud` or `custom`.
  The `cloud` target is used to interact with the Veridas cloud APIs.
  The `custom` target is used to interact with self-hosted or on-premises
  Veridas APIs.

  If you want to use it with the `custom` target, don't need to care about the
  rest of the parameters, but you must provide the `url`.

  Default: `cloud`.

- `url`: the URL of the API to interact with. It is only used when the `target`
  is `custom`.

- `apikey`: the API key to use for the requests against the Veridas Cloud API.

- `environment`: the environment to use for the requests. It can be `production`
  or `sandbox`.

  Default: `sandbox`.

- `location`: the location to use for the requests. It can be `eu` or `us`,
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
    target="cloud",
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

- `VERICLIENT_TARGET`: The target API to use.
- `VERICLIENT_ENVIRONMENT`: The environment to use for the requests.
- `VERICLIENT_APIKEY`: The API key to use for the requests against the Veridas Cloud API.
- `VERICLIENT_LOCATION`: The location to use for the requests.
- `VERICLIENT_URL`: In case you want to use a self-hosted API, you can set the URL with this variable.
- `VERICLIENT_TIMEOUT`: The timeout for the requests.
