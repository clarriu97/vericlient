import pytest
from vericlient import DaspeakClient
from vericlient.daspeak.models import (
    CompareAudio2AudioInput,
    CompareAudio2AudioOutput,
    CompareAudio2CredentialsInput,
    CompareAudio2CredentialsOutput,
    CompareCredential2AudioInput,
    CompareCredential2AudioOutput,
    CompareCredential2CredentialInput,
    CompareCredential2CredentialOutput,
    CompareCredential2CredentialsInput,
    CompareCredential2CredentialsOutput,
    GenerateCredentialInput,
    GenerateCredentialOutput,
)


def test_daspeak_alive(mock_server, daspeak_alive_parameters):
    for param in daspeak_alive_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        if mock_server:
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        response = daspeak_client.alive()

        assert response


def test_daspeak_get_models(mock_server, daspeak_get_models_parameters):
    for param in daspeak_get_models_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        if mock_server:
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
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
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
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


def _test_error(        # noqa: ANN202
    mock_server, daspeak_generate_credential_error_response_parameters, audio_file,
):
    for param in daspeak_generate_credential_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
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
            audio=audio_file,
            hash=model,
        )
        with pytest.raises(exception):
            daspeak_client.generate_credential(input_model)


def test_daspeak_generate_credential_too_many_audio_channels_error(
    mock_server, daspeak_generate_credential_channels_error_response_parameters, audio_too_many_channels_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_channels_error_response_parameters,
        audio_too_many_channels_file,
    )

def test_daspeak_generate_credential_sample_rate_error(
    mock_server, daspeak_generate_credential_sample_rate_error_response_parameters, audio_invalid_sample_rate_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_sample_rate_error_response_parameters,
        audio_invalid_sample_rate_file,
    )


def test_daspeak_generate_credential_net_speech_error(
    mock_server, daspeak_generate_credential_net_speech_duration_error_response_parameters, audio_not_enough_speech_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_net_speech_duration_error_response_parameters,
        audio_not_enough_speech_file,
    )


def test_daspeak_generate_credential_bad_snr_error(
    mock_server, daspeak_generate_credential_bad_snr_error_response_parameters, audio_bad_snr_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_bad_snr_error_response_parameters,
        audio_bad_snr_file,
    )


def test_daspeak_generate_credential_audio_too_long_error(
    mock_server, daspeak_generate_credential_audio_too_long_error_response_parameters, audio_too_long_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_audio_too_long_error_response_parameters,
        audio_too_long_file,
    )


def test_daspeak_generate_credentail_codec_error(
    mock_server, daspeak_generate_credential_codec_error_response_parameters, audio_codec_error_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_codec_error_response_parameters,
        audio_codec_error_file,
    )


def test_daspeak_generate_credential_insufficient_quality_error(
    mock_server, daspeak_generate_credential_insufficient_quality_error_response_parameters, audio_insufficient_quality_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_insufficient_quality_error_response_parameters,
        audio_insufficient_quality_file,
    )


def test_daspeak_generate_credential_invalid_specified_channel_error(
    mock_server, daspeak_generate_credential_invalid_specified_channel_error_response_parameters, audio_file,
):
    for param in daspeak_generate_credential_invalid_specified_channel_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
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
            audio=audio_file,
            hash=model,
            channel=100,
        )
        with pytest.raises(exception):
            daspeak_client.generate_credential(input_model)


def test_daspeak_generate_credential_calibration_not_available_error(
    mock_server, daspeak_generate_credential_calibration_not_available_error_response_parameters, audio_file,
):
    for param in daspeak_generate_credential_calibration_not_available_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
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
            audio=audio_file,
            hash=model,
            calibration="invalid-calibration",
        )
        with pytest.raises(exception):
            daspeak_client.generate_credential(input_model)


def test_daspeak_generate_credential_unsupported_media_type_error(
    mock_server, daspeak_generate_credential_unsupported_media_type_error_response_parameters, audio_unsupported_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_unsupported_media_type_error_response_parameters,
        audio_unsupported_file,
    )


def test_daspeak_server_error(
    mock_server, daspeak_server_error_response_parameters, audio_file,
):
    for param in daspeak_server_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"

            input_model = GenerateCredentialInput(
                audio=audio_file,
                hash=model,
            )
            with pytest.raises(exception):
                daspeak_client.generate_credential(input_model)


def test_daspeak_compare_credential2audio(
    mock_server, daspeak_compare_credential2audio_parameters, audio_file_path, audio_file,
):
    for param in daspeak_compare_credential2audio_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
            credential_reference = "fake-credential"
        else:
            model = daspeak_client.get_models().models[-1]
            credential_reference = daspeak_client.generate_credential(
                GenerateCredentialInput(audio=audio_file_path, hash=model),
            ).credential

        input_model = CompareCredential2AudioInput(
            audio_to_evaluate=audio_file_path,
            credential_reference=credential_reference,
        )
        response = daspeak_client.compare(input_model)
        assert isinstance(response, CompareCredential2AudioOutput)

        input_model = CompareCredential2AudioInput(
            audio_to_evaluate=audio_file,
            credential_reference=credential_reference,
        )
        response = daspeak_client.compare(input_model)
        assert isinstance(response, CompareCredential2AudioOutput)


def test_daspeak_compare_audio2audio(
    mock_server, daspeak_compare_audio2audio_parameters, audio_file,
):
    for param in daspeak_compare_audio2audio_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        input_model = CompareAudio2AudioInput(
            audio_to_evaluate=audio_file,
            audio_reference=audio_file,
            hash=model,
        )
        response = daspeak_client.compare(input_model)
        assert isinstance(response, CompareAudio2AudioOutput)


def test_daspeak_compare_credential2credential(
    mock_server, daspeak_compare_credential2credential_parameters, audio_file,
):
    for param in daspeak_compare_credential2credential_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
            credential_reference = "fake-credential"
        else:
            model = daspeak_client.get_models().models[-1]
            credential_reference = daspeak_client.generate_credential(
                GenerateCredentialInput(audio=audio_file, hash=model),
            ).credential

        input_model = CompareCredential2CredentialInput(
            credential_to_evaluate=credential_reference,
            credential_reference=credential_reference,
        )
        response = daspeak_client.compare(input_model)
        assert isinstance(response, CompareCredential2CredentialOutput)


def test_daspeak_compare_audio2credentials(
    mock_server, daspeak_compare_audio2credentials_parameters, audio_file,
):
    for param in daspeak_compare_audio2credentials_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
            credential_list = [("id1", "fake-credential1"), ("id2", "fake-credential2")]
        else:
            model = daspeak_client.get_models().models[-1]
            credential = daspeak_client.generate_credential(GenerateCredentialInput(audio=audio_file, hash=model)).credential
            credential_list = [("id1", credential), ("id2", credential)]

        input_model = CompareAudio2CredentialsInput(
            audio_reference=audio_file,
            credential_list=credential_list,
        )
        response = daspeak_client.compare(input_model)
        assert isinstance(response, CompareAudio2CredentialsOutput)


def test_daspeak_client_compare_credential2credentials(
    mock_server, daspeak_compare_credential2credentials_parameters, audio_file,
):
    for param in daspeak_compare_credential2credentials_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
            credential = "fake-credential"
            credential_list = [("id1", "fake-credential1"), ("id2", "fake-credential2")]
        else:
            model = daspeak_client.get_models().models[-1]
            credential = daspeak_client.generate_credential(GenerateCredentialInput(audio=audio_file, hash=model)).credential
            credential_list = [("id1", credential), ("id2", credential)]

        response = daspeak_client.compare(CompareCredential2CredentialsInput(
            credential_reference=credential,
            credential_list=credential_list,
        ))
        assert isinstance(response, CompareCredential2CredentialsOutput)


def test_daspeak_client_compare_with_invalid_object_type():
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    with pytest.raises(TypeError):
        daspeak_client.compare(data_model="invalid-object-type")


def test_daspeak_client_invalid_file_path():
    invalid_audio_file_path = "invalid-file-path"
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    with pytest.raises(FileNotFoundError) as excinfo:
        daspeak_client.generate_credential(GenerateCredentialInput(audio="invalid-file-path", hash="fake-hash"))
    assert f"File {invalid_audio_file_path} not found" in str(excinfo.value)
