import pytest
from pydantic import ValidationError

from vericlient import DaspeakClient
from vericlient.daspeak.exceptions import ModelNotAvailableError
from vericlient.daspeak.models import (
    CompareAudio2AudioOutput,
    CompareAudio2CredentialsOutput,
    CompareCredential2AudioOutput,
    CompareCredential2CredentialInput,
    CompareCredential2CredentialOutput,
    CompareCredential2CredentialsOutput,
    GenerateCredentialOutput,
    GetModelCalibrationsOutput,
    GetModelMetadataFromCredentialOutput,
    GetModelMetadataInput,
    GetModelMetadataOutput,
)


def _sent_body(mock_server) -> str:
    """Return the last request body as text, tolerating raw audio in a multipart body."""
    body = mock_server.last_request.body
    return body.decode("latin-1") if isinstance(body, bytes) else body


@pytest.mark.daspeak
def test_daspeak_alive(mock_server, daspeak_alive_parameters):
    for param in daspeak_alive_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        if mock_server:
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        response = daspeak_client.alive()

        assert response


@pytest.mark.daspeak
def test_daspeak_get_models(mock_server, daspeak_get_models_parameters):
    for param in daspeak_get_models_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        if mock_server:
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        response = daspeak_client.get_models()

        if mock_server:
            assert response.models == mock_response["models"]
        else:
            assert isinstance(response.models, list)


@pytest.mark.daspeak
def test_daspeak_get_model_metadata(mock_server, daspeak_get_model_metadata_parameters):
    for param in daspeak_get_model_metadata_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-hash"
        else:
            model = daspeak_client.get_models().models[-1]

        response = daspeak_client.get_model_metadata(hash=model)

        assert isinstance(response, GetModelMetadataOutput)
        assert response.metadata.hash == model
        assert response.metadata.description


@pytest.mark.daspeak
def test_daspeak_get_model_calibrations(mock_server, daspeak_get_model_calibrations_parameters):
    for param in daspeak_get_model_calibrations_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-hash"
        else:
            model = daspeak_client.get_models().models[-1]

        response = daspeak_client.get_model_calibrations(hash=model)

        assert isinstance(response, GetModelCalibrationsOutput)
        assert response.calibrations
        # Whatever the service reports has to be usable as a `calibration` argument.
        assert "telephone-channel" in response.calibrations


@pytest.mark.daspeak
def test_daspeak_get_model_metadata_from_credential(
    mock_server,
    daspeak_get_model_metadata_from_credential_parameters,
    audio_file,
):
    for param in daspeak_get_model_metadata_from_credential_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            credential = "fake-credential"
            model = "fake-hash"
        else:
            model = daspeak_client.get_models().models[-1]
            credential = daspeak_client.generate_credential(
                audio=audio_file,
                hash=model,
            ).credential

        response = daspeak_client.get_model_metadata_from_credential(
            credential=credential,
        )

        assert isinstance(response, GetModelMetadataFromCredentialOutput)
        # The credential was generated with that model, so the metadata must point back to it.
        assert response.metadata.hash == model


@pytest.mark.daspeak
def test_daspeak_get_model_metadata_unknown_hash(mock_server, daspeak_model_not_available_parameters):
    for param in daspeak_model_not_available_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        with pytest.raises(exception or ModelNotAvailableError):
            daspeak_client.get_model_metadata(hash="not-a-real-hash")


@pytest.mark.daspeak
def test_daspeak_generate_credential(mock_server, daspeak_generate_credential_parameters, audio_file_path, audio_file):
    for param in daspeak_generate_credential_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        response = daspeak_client.generate_credential(audio=audio_file_path, hash=model)
        assert isinstance(response, GenerateCredentialOutput)

        response = daspeak_client.generate_credential(audio=audio_file, hash=model)
        assert isinstance(response, GenerateCredentialOutput)


def _test_error(  # noqa: ANN202
    mock_server,
    daspeak_generate_credential_error_response_parameters,
    audio_file,
):
    for param in daspeak_generate_credential_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        with pytest.raises(exception):
            daspeak_client.generate_credential(audio=audio_file, hash=model)


@pytest.mark.daspeak
def test_daspeak_generate_credential_too_many_audio_channels_error(
    mock_server,
    daspeak_generate_credential_channels_error_response_parameters,
    audio_too_many_channels_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_channels_error_response_parameters,
        audio_too_many_channels_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_sample_rate_error(
    mock_server,
    daspeak_generate_credential_sample_rate_error_response_parameters,
    audio_invalid_sample_rate_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_sample_rate_error_response_parameters,
        audio_invalid_sample_rate_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_net_speech_error(
    mock_server,
    daspeak_generate_credential_net_speech_duration_error_response_parameters,
    audio_not_enough_speech_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_net_speech_duration_error_response_parameters,
        audio_not_enough_speech_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_bad_snr_error(
    mock_server,
    daspeak_generate_credential_bad_snr_error_response_parameters,
    audio_bad_snr_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_bad_snr_error_response_parameters,
        audio_bad_snr_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_audio_too_long_error(
    mock_server,
    daspeak_generate_credential_audio_too_long_error_response_parameters,
    audio_too_long_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_audio_too_long_error_response_parameters,
        audio_too_long_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credentail_codec_error(
    mock_server,
    daspeak_generate_credential_codec_error_response_parameters,
    audio_codec_error_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_codec_error_response_parameters,
        audio_codec_error_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_insufficient_quality_error(
    mock_server,
    daspeak_generate_credential_insufficient_quality_error_response_parameters,
    audio_insufficient_quality_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_insufficient_quality_error_response_parameters,
        audio_insufficient_quality_file,
    )


@pytest.mark.daspeak
def test_daspeak_generate_credential_invalid_specified_channel_error(
    mock_server,
    daspeak_generate_credential_invalid_specified_channel_error_response_parameters,
    audio_file,
):
    for param in daspeak_generate_credential_invalid_specified_channel_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        with pytest.raises(exception):
            daspeak_client.generate_credential(audio=audio_file, hash=model, channel=100)


@pytest.mark.daspeak
def test_daspeak_generate_credential_calibration_not_available_error(
    mock_server,
    daspeak_generate_credential_calibration_not_available_error_response_parameters,
    audio_file,
):
    for param in daspeak_generate_credential_calibration_not_available_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"
        else:
            model = daspeak_client.get_models().models[-1]

        with pytest.raises(exception):
            daspeak_client.generate_credential(audio=audio_file, hash=model, calibration="invalid-calibration")


@pytest.mark.daspeak
def test_daspeak_generate_credential_unsupported_media_type_error(
    mock_server,
    daspeak_generate_credential_unsupported_media_type_error_response_parameters,
    audio_unsupported_file,
):
    _test_error(
        mock_server,
        daspeak_generate_credential_unsupported_media_type_error_response_parameters,
        audio_unsupported_file,
    )


@pytest.mark.daspeak
def test_daspeak_server_error(
    mock_server,
    daspeak_server_error_response_parameters,
    audio_file,
):
    for param in daspeak_server_error_response_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, exception = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)
            model = "fake-model"

            with pytest.raises(exception):
                daspeak_client.generate_credential(audio=audio_file, hash=model)


@pytest.mark.daspeak
def test_daspeak_compare_credential2audio(
    mock_server,
    daspeak_compare_credential2audio_parameters,
    audio_file_path,
    audio_file,
):
    for param in daspeak_compare_credential2audio_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
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
                audio=audio_file_path,
                hash=model,
            ).credential

        response = daspeak_client.compare_credential_to_audio(
            audio_to_evaluate=audio_file_path,
            credential_reference=credential_reference,
        )
        assert isinstance(response, CompareCredential2AudioOutput)

        response = daspeak_client.compare_credential_to_audio(
            audio_to_evaluate=audio_file,
            credential_reference=credential_reference,
        )
        assert isinstance(response, CompareCredential2AudioOutput)


@pytest.mark.daspeak
def test_daspeak_compare_audio2audio(
    mock_server,
    daspeak_compare_audio2audio_parameters,
    audio_file,
):
    for param in daspeak_compare_audio2audio_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
            environment=environment,
            location=location,
            url=url,
        )
        if mock_server:
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        # No model is named here: this endpoint compares two recordings directly. The old
        # call passed `hash=`, which this input never had and pydantic silently dropped.
        response = daspeak_client.compare_audio_to_audio(
            audio_reference=audio_file,
            audio_to_evaluate=audio_file,
        )
        assert isinstance(response, CompareAudio2AudioOutput)


@pytest.mark.daspeak
def test_daspeak_compare_credential2credential(
    mock_server,
    daspeak_compare_credential2credential_parameters,
    audio_file,
):
    for param in daspeak_compare_credential2credential_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
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
                audio=audio_file,
                hash=model,
            ).credential

        response = daspeak_client.compare_credential_to_credential(
            credential_to_evaluate=credential_reference,
            credential_reference=credential_reference,
        )
        assert isinstance(response, CompareCredential2CredentialOutput)


@pytest.mark.daspeak
def test_daspeak_compare_audio2credentials(
    mock_server,
    daspeak_compare_audio2credentials_parameters,
    audio_file,
):
    for param in daspeak_compare_audio2credentials_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
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
            credential = daspeak_client.generate_credential(audio=audio_file, hash=model).credential
            credential_list = [("id1", credential), ("id2", credential)]

        response = daspeak_client.identify_audio(
            audio_to_evaluate=audio_file,
            credential_list=credential_list,
        )
        assert isinstance(response, CompareAudio2CredentialsOutput)

        if mock_server:
            # The API names this field `audio_to_evaluate`; sending `audio_reference`
            # returns 400 NoAudioException, which no URL-only mock would catch.
            assert 'name="audio_to_evaluate"' in _sent_body(mock_server)


@pytest.mark.daspeak
def test_daspeak_client_compare_credential2credentials(
    mock_server,
    daspeak_compare_credential2credentials_parameters,
    audio_file,
):
    for param in daspeak_compare_credential2credentials_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        daspeak_client = DaspeakClient(
            apikey="fake-apikey" if mock_server else None,
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
            credential = daspeak_client.generate_credential(audio=audio_file, hash=model).credential
            credential_list = [("id1", credential), ("id2", credential)]

        response = daspeak_client.identify_credential(
            credential_to_evaluate=credential,
            credential_list=credential_list,
        )
        assert isinstance(response, CompareCredential2CredentialsOutput)

        if mock_server:
            # Likewise: the API names this field `credential_to_evaluate`.
            assert "credential_to_evaluate" in _sent_body(mock_server)


@pytest.mark.daspeak
def test_daspeak_client_compare_with_invalid_object_type():
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    with pytest.raises(TypeError):
        daspeak_client.compare(data_model="invalid-object-type")


@pytest.mark.daspeak
def test_daspeak_client_invalid_file_path():
    invalid_audio_file_path = "invalid-file-path"
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    with pytest.raises(FileNotFoundError) as excinfo:
        daspeak_client.generate_credential(audio="invalid-file-path", hash="fake-hash")
    assert f"File {invalid_audio_file_path} not found" in str(excinfo.value)


@pytest.mark.daspeak
def test_compare_still_dispatches_and_warns(mock_server, daspeak_compare_credential2credential_parameters):
    """`compare()` is deprecated, and has to keep working until 1.0.0.

    It is the one method the change could not convert mechanically: it chose between five
    comparisons by the *type* of the model handed to it, so it could not be called at all
    without importing one of five classes. Each of them is a method with a name now, and
    the warning says which.
    """
    if not mock_server:
        pytest.skip("Covered against the real service by the five methods it dispatches to")

    endpoint, mock_response, mock_status_code, *_ = daspeak_compare_credential2credential_parameters[0]
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

    with pytest.warns(DeprecationWarning, match="compare_credential_to_credential"):
        response = daspeak_client.compare(
            CompareCredential2CredentialInput(
                credential_reference="a-credential",
                credential_to_evaluate="another-credential",
            ),
        )

    assert isinstance(response, CompareCredential2CredentialOutput)


@pytest.mark.daspeak
def test_the_old_call_style_still_works_and_warns(mock_server, daspeak_get_model_metadata_parameters):
    if not mock_server:
        pytest.skip("Asserted on the request the client builds")

    endpoint, mock_response, mock_status_code, *_ = daspeak_get_model_metadata_parameters[0]
    daspeak_client = DaspeakClient(apikey="fake-apikey")
    mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

    with pytest.warns(DeprecationWarning, match="GetModelMetadataInput"):
        daspeak_client.get_model_metadata(GetModelMetadataInput(hash="a-hash"))


@pytest.mark.daspeak
def test_daspeak_input_errors_name_the_method():
    """The caller wrote `generate_credential(...)`, so that is what the error says."""
    daspeak_client = DaspeakClient(apikey="fake-apikey")

    with pytest.raises(ValidationError) as raised:
        daspeak_client.generate_credential(audio=123, hash="a-hash")

    assert len(raised.value.errors()) == 1
    assert "expected a path to a file, or its content as bytes" in str(raised.value)
    assert "generate_credential()" in str(raised.value)
    assert "GenerateCredentialInput" not in str(raised.value)
