import pytest

from vericlient.daspeak.client import DaspeakClient
from vericlient.environments import Target, Environments, Locations


@pytest.mark.parametrize(
    "endpoint, mock_response, mock_status_code, url, target, environment, location",
    [
        ('https://api-work.eu.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value),
        ('https://api.eu.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value),
        ('https://api-work.us.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value),
        ('https://api.us.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value),
        ('https://custom-daspeak-url.com/alive', "", 200, "https://custom-daspeak-url.com", None, None, None),
    ]
)
def test_daspeak_alive(mock_server, endpoint, mock_response, mock_status_code, url, target, environment, location):
    if mock_server:
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    daspeak_client = DaspeakClient(
        apikey="fake-apikey",
        target=target,
        environment=environment,
        location=location,
        url=url,
    )
    response = daspeak_client.alive()

    assert response


@pytest.mark.parametrize(
    "endpoint, mock_response, mock_status_code, url, target, environment, location",
    [
        ('https://api-work.eu.veri-das.com/daspeak/v1/models', {"version": "", "models": ["model1", "model2"]}, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value),
    ]
)
def test_daspeak_get_models(mock_server, endpoint, mock_response, mock_status_code, url, target, environment, location):
    if mock_server:
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    daspeak_client = DaspeakClient(
        apikey="fake-apikey",
        target=target,
        environment=environment,
        location=location,
        url=url,
    )
    response = daspeak_client.get_models()

    if mock_server:
        assert response.models == mock_response["models"]
    else:
        assert isinstance(response.models, list)
