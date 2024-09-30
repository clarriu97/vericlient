# VCSP Client usage

This is an example of how to use the
[VCSP](https://docs.veridas.com/vcsp/cloud/latest/) client:

## Check if the API is alive

```python
from vericlient import VcspClient

client = VcspClient(apikey="your_api_key")

print(f"Alive: {client.alive()}")
```
