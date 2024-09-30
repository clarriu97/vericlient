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
from vericlient.exceptions import (
    ServerError,
    UnsupportedMediaTypeError,
)

from tests.conftest import provide_testing_parameters


@pytest.fixture(scope="session")
def service_name():
    return "daspeak"


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

@pytest.fixture(scope="session")
def daspeak_alive_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_alive_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/alive", \
        daspeak_alive_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_get_models_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_get_models_response,
        service_name,
    )-> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models", \
        daspeak_get_models_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_generate_credential_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_generate_credential_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_channels_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_channels_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_channels_error_response, 400, TooManyAudioChannelsError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_sample_rate_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_sample_rate_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_sample_rate_error_response, 400, UnsupportedSampleRateError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_net_speech_duration_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_net_speech_duration_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_net_speech_duration_error_response, 400, NetSpeechDurationIsNotEnoughError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_bad_snr_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_snr_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_snr_error_response, 400, SignalNoiseRatioError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_audio_too_long_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_long_audio_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_long_audio_error_response, 400, AudioDurationTooLongError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_codec_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_codec_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_codec_error_response, 400, UnsupportedAudioCodecError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_insufficient_quality_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_quality_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_quality_error_response, 400, InsufficientQualityError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_invalid_specified_channel_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_invalid_specified_channel_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_invalid_specified_channel_error_response, 400, InvalidSpecifiedChannelError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_calibration_not_available_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_calibration_not_available_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_calibration_not_available_error_response, 400, CalibrationNotAvailableError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_generate_credential_unsupported_media_type_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_unsupported_media_type_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_unsupported_media_type_error_response, 415, UnsupportedMediaTypeError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_server_error_response_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_server_error_response,
        service_name,
    ):
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/models/fake-model/credential/wav", \
        daspeak_server_error_response, 500, ServerError, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2audio_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2audio_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/credential2wav", \
        daspeak_compare_credential2audio_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_compare_audio2audio_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_audio2audio_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/wav2wav", \
        daspeak_compare_audio2audio_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2credential_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/similarity/credential2credential", \
        daspeak_compare_credential2credential_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_compare_audio2credentials_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_audio2credentials_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/identification/wav2credentials", \
        daspeak_compare_audio2credentials_response, 200, None, service_name,
    )


@pytest.fixture(scope="session")
def daspeak_compare_credential2credentials_parameters(
        mock_option,
        test_environment,
        all_environments,
        daspeak_compare_credential2credentials_response,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment, all_environments, mock_option, "daspeak/v1/identification/credential2credentials", \
        daspeak_compare_credential2credentials_response, 200, None, service_name,
    )
