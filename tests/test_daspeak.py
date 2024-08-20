import pytest

from vericlient import DaspeakClient
from vericlient.environments import Target, Environments, Locations



def test_daspeak_alive(mock_server, daspeak_alive_parameters):
    for param in daspeak_alive_parameters:
        endpoint, mock_response, mock_status_code, url, target, environment, location = param
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


def test_daspeak_get_models(mock_server, daspeak_get_models_parameters):
    for param in daspeak_get_models_parameters:
        endpoint, mock_response, mock_status_code, url, target, environment, location = param
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
