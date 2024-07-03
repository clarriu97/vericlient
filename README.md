# Welcome

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
from vericlient import VericlientFactory, APIs

# Create a factory instance
factory = VericlientFactory()

# Create a client for the das-Peak API
daspeak_client = factory.create_client(APIs.DAS_PEAK, api_key='your-api-key')

# Test the connection
print(daspeak_client.alive())
```

You can also use the client against any self-hosted Veridas API:

```python
from vericlient import VericlientFactory

# Create a factory instance
factory = VericlientFactory()

# Create a client for the das-Peak API
daspeak_client = factory.create_client(url="https://your-self-hosted-api.com")

# Test the connection
print(daspeak_client.alive())
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
