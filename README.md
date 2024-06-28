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
| das-Peak |       🟢      |
| VCSP     |       🔴      |
| das-Face |       🟠      |

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

# Configuration

The library can be configured using environment variables.
The following variables are supported:

- `VERICLIENT_APIKEY`: The API key to use for the requests.
- `VERICLIENT_ENVIRONMENT`: The environment to use for the requests (default: `production`).
- `VERICLIENT_TIMEOUT`: The timeout for the requests (default: `10`).
