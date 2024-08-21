from vericlient import DaspeakClient
from vericlient.daspeak.models import (
    GenerateCredentialInput,
    GenerateCredentialOutput,
)


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


def test_daspeak_generate_credential(mock_server, daspeak_generate_credential_parameters, audio_file_path, audio_file):
    for param in daspeak_generate_credential_parameters:
        endpoint, mock_response, mock_status_code, url, target, environment, location = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            target=target,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        input_model = GenerateCredentialInput(
            audio=audio_file_path,
            hash=model,
        )
        response = daspeak_client.generate_credential(input_model)
        assert isinstance(response, GenerateCredentialOutput)

        input_model = GenerateCredentialInput(
            audio=audio_file,
            hash=model,
        )
        response = daspeak_client.generate_credential(input_model)
        assert isinstance(response, GenerateCredentialOutput)
