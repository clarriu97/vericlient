import pytest
from vericlient.daspeak.exceptions import (
    AudioDurationTooLongError,
    CalibrationNotAvailableError,
    InsufficientQualityError,
    InvalidSpecifiedChannelError,
    NetSpeechDurationIsNotEnoughError,
    SignalNoiseRatioError,
    TooManyAudioChannelsError,
    UnsupportedAudioCodecError,
    UnsupportedSampleRateError,
)
from vericlient.environments import Environments, Locations
from vericlient.exceptions import (
    ServerError,
    UnsupportedMediaTypeError,
)

from tests.conftest import (
    eu_production_test_env,
    eu_sandbox_url,
    eu_sandobox_test_env,
    ue_production_url,
    us_production_test_env,
    us_production_url,
    us_sandbox_test_env,
    us_sandbox_url,
)

####################
# SERVER RESPONSES #
####################

@pytest.fixture(scope="session")
def daspeak_alive_response():
    return ""


@pytest.fixture(scope="session")
def daspeak_get_models_response():
    return {"version": "1", "models": ["model1", "model2"]}


@pytest.fixture(scope="session")
def daspeak_generate_credential_response():
    return {
        "version": "1",
        "model": {
            "hash": "fake-hash",
            "mode": "fake-mode",
        },
        "credential": "fake-credential",
        "authenticity": 0.99,
        "input_audio_duration": 5.00,
        "net_speech_duration": 4.50,
    }


@pytest.fixture(scope="session")
def daspeak_compare_credential2audio_response():
    return {
        "version": "1",
        "score": 0.99,
        "model": {
            "hash": "fake-hash",
            "mode": "fake-mode",
        },
        "calibration": "fake-calibration",
        "authenticity_to_evaluate": 0.99,
        "input_audio_duration_to_evaluate": 5.00,
        "net_speech_duration_to_evaluate": 4.50,
    }


@pytest.fixture(scope="session")
def daspeak_compare_audio2audio_response():
    return {
        "version": "1",
        "score": 0.99,
        "model": {
            "hash": "fake-hash",
            "mode": "fake-mode",
        },
        "calibration": "fake-calibration",
        "authenticity_to_evaluate": 0.99,
        "authenticity_reference": 0.99,
        "input_audio_duration_to_evaluate": 5.00,
        "input_audio_duration_reference": 5.00,
        "net_speech_duration_to_evaluate": 4.50,
        "net_speech_duration_reference": 4.50,
    }


@pytest.fixture(scope="session")
def daspeak_compare_credential2credential_response():
    return {
        "version": "1",
        "score": 0.99,
        "model": {
            "hash": "fake-hash",
            "mode": "fake-mode",
        },
        "calibration": "fake-calibration",
    }


@pytest.fixture(scope="session")
def daspeak_compare_audio2credentials_response():
    return {
        "version": "1",
        "model": {
            "hash": "fake-hash",
            "mode": "fake-mode",
        },
        "calibration": "fake-calibration",
        "authenticity_reference": 0.99,
        "scores": [
            {
                "id": "fake-id1",
                "score": 0.99,
            },
            {
                "id": "fake-id2",
                "score": 0.97,
            },
        ],
        "result": {
            "id": "fake-id1",
            "score": 0.99,
        },
        "input_audio_duration_reference": 5.00,
        "net_speech_duration_reference": 4.50,
    }


@pytest.fixture(scope="session")
def daspeak_compare_credential2credentials_response():
    return {
        "version": "1",
        "calibration": "fake-calibration",
        "scores": [
            {
                "id": "fake-id1",
                "score": 0.99,
            },
            {
                "id": "fake-id2",
                "score": 0.97,
            },
        ],
        "result": {
            "id": "fake-id1",
            "score": 0.99,
        },
    }


#################
# SERVER ERRORS #
#################

@pytest.fixture(scope="session")
def daspeak_channels_error_response():
    return {
        "error": "The wav has more channels than are accepted by the system",
        "exception": "AudioInputException",
    }


@pytest.fixture(scope="session")
def daspeak_sample_rate_error_response():
    return {
        "error": "The sample rate is not supported, must be 8 Khz or 16 Khz",
        "exception": "AudioInputException",
    }


@pytest.fixture(scope="session")
def daspeak_codec_error_response():
    return {
        "error": "Provided audio data uses an unsupported codec. Supported codecs are:",
        "exception": "AudioInputException",
    }


@pytest.fixture(scope="session")
def daspeak_long_audio_error_response():
    return {
        "error": "The wav duration is longer than 30 seconds",
        "exception": "AudioInputException",
    }


@pytest.fixture(scope="session")
def daspeak_snr_error_response():
    return {
        "error": "Noise level exceeded",
        "exception": "SignalNoiseRatioException",
    }


@pytest.fixture(scope="session")
def daspeak_net_speech_duration_error_response():
    return {
        "error": "Voice duration is not enough 2.55s < 3.00s",
        "exception": "VoiceDurationIsNotEnoughException",
    }


@pytest.fixture(scope="session")
def daspeak_invalid_specified_channel_error_response():
    return {
        "error": "Invalid specified channel/s",
        "exception": "InvalidChannelException",
    }


@pytest.fixture(scope="session")
def daspeak_quality_error_response():
    return {
        "error": "The audio quality is not good enough",
        "exception": "InsufficientQuality",
    }


@pytest.fixture(scope="session")
def daspeak_calibration_not_available_error_response():
    return {
        "error": "The calibration <calibration> is not available",
        "exception": "CalibrationNotAvailable",
    }


@pytest.fixture(scope="session")
def daspeak_invalid_credential_error_response():
    return {
        "error": "Decryption error",
        "exception": "InvalidCredential",
    }


@pytest.fixture(scope="session")
def daspeak_unsupported_media_type_error_response():
    return {
        "error": "415 Unsupported Media Type: The server does not support the media type transmitted in the request",
        "exception": "UnsupportedMediaType",
    }


@pytest.fixture(scope="session")
def daspeak_server_error_response():
    return {
        "error": "An internal server error occured",
        "exception": "DaspeakInternalException",
    }


#######################
# PARAMETERS FIXTURES #
#######################

def _provide_daspeak_parameters(
        test_environment: str,
        all_environments: list,
        mock_option: bool,      # noqa: FBT001
        endpoint: str,
        response: dict,
        status_code: int,
        exception: Exception,
    ) -> list:
    """Provide the parameters necessary for Daspekea testing depending on the test environment.

    Those parameters are:
    - endpoint: the endpoint to test
    - response: the response to return
    - status_code: the status code to return
    - exception: the exception to raise if any

    The parameters are returned as a list of tuples, each tuple containing the parameters for a specific environment.

    """
    ue_sandbox = (f"{eu_sandbox_url}/{endpoint}", response, status_code, None, \
        Environments.SANDBOX.value, Locations.EU.value, exception)
    ue_production = (f"{ue_production_url}/{endpoint}", response, status_code, None, \
        Environments.PRODUCTION.value, Locations.EU.value, exception)
    us_sandbox = (f"{us_sandbox_url}/{endpoint}", response, status_code, None, \
        Environments.SANDBOX.value, Locations.US.value, exception)
    us_production = (f"{us_production_url}/{endpoint}", response, status_code, None, \
        Environments.PRODUCTION.value, Locations.US.value, exception)
    if mock_option:
        parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            (f"https://custom-daspeak-url.com/{endpoint}", response, status_code, \
                "https://custom-daspeak-url.com/daspeak/v1", None, None, exception),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == eu_sandobox_test_env:
        parameters = [ue_sandbox]
    elif test_environment == eu_production_test_env:
        parameters = [ue_production]
    elif test_environment == us_sandbox_test_env:
        parameters = [us_sandbox]
    elif test_environment == us_production_test_env:
        parameters = [us_production]
    return parameters


@pytest.fixture(scope="session")
def daspeak_alive_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_alive_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/alive", \
        daspeak_alive_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_get_models_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_get_models_response,
    )-> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models", \
        daspeak_get_models_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_generate_credential_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_generate_credential_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_channels_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_channels_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_channels_error_response, 400, TooManyAudioChannelsError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_sample_rate_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_sample_rate_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_sample_rate_error_response, 400, UnsupportedSampleRateError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_net_speech_duration_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_net_speech_duration_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_net_speech_duration_error_response, 400, NetSpeechDurationIsNotEnoughError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_bad_snr_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_snr_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_snr_error_response, 400, SignalNoiseRatioError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_audio_too_long_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_long_audio_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_long_audio_error_response, 400, AudioDurationTooLongError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_codec_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_codec_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_codec_error_response, 400, UnsupportedAudioCodecError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_insufficient_quality_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_quality_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_quality_error_response, 400, InsufficientQualityError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_invalid_specified_channel_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_invalid_specified_channel_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_invalid_specified_channel_error_response, 400, InvalidSpecifiedChannelError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_calibration_not_available_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_calibration_not_available_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_calibration_not_available_error_response, 400, CalibrationNotAvailableError,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_unsupported_media_type_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_unsupported_media_type_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_unsupported_media_type_error_response, 415, UnsupportedMediaTypeError,
    )


@pytest.fixture(scope="session")
def daspeak_server_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_server_error_response,
    ):
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_server_error_response, 500, ServerError,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2audio_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2audio_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/credential2wav", \
        daspeak_compare_credential2audio_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_compare_audio2audio_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_audio2audio_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/wav2wav", \
        daspeak_compare_audio2audio_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2credential_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/credential2credential", \
        daspeak_compare_credential2credential_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_compare_audio2credentials_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_audio2credentials_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/identification/wav2credentials", \
        daspeak_compare_audio2credentials_response, 200, None,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2credentials_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2credentials_response,
    ) -> list:
    return _provide_daspeak_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/identification/credential2credentials", \
        daspeak_compare_credential2credentials_response, 200, None,
    )


######################
# RESOURCES FIXTURES #
######################

@pytest.fixture(scope="session")
def audio_file_path() -> str:
    return "tests/daspeak/resources/audio.wav"


@pytest.fixture(scope="session")
def audio_file() -> bytes:
    with open("tests/daspeak/resources/audio.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_spoof_file() -> bytes:
    with open("tests/daspeak/resources/audio_spoof.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_not_enough_speech_file() -> bytes:
    with open("tests/daspeak/resources/audio_not_enough_speech.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_bad_snr_file() -> bytes:
    with open("tests/daspeak/resources/audio_bad_snr.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_insufficient_quality_file() -> bytes:
    with open("tests/daspeak/resources/audio_insufficient_quality.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_too_many_channels_file() -> bytes:
    with open("tests/daspeak/resources/audio_too_many_channels.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_invalid_sample_rate_file() -> bytes:
    with open("tests/daspeak/resources/audio_invalid_sample_rate.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_too_long_file() -> bytes:
    with open("tests/daspeak/resources/audio_too_long.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_codec_error_file() -> bytes:
    with open("tests/daspeak/resources/audio_codec_error.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_unsupported_file() -> bytes:
    with open("tests/__init__.py", "rb") as f:
        return f.read()
