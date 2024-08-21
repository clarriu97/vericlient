import pytest

from vericlient.environments import Target, Environments, Locations
from tests.conftest import (
    eu_sandbox_url,
    ue_production_url,
    us_sandbox_url,
    us_production_url,
    eu_sandobox_test_env,
    eu_production_test_env,
    us_sandbox_test_env,
    us_production_test_env,
)


# server responses OK

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
            "mode": "fake-mode"
        },
        "credential": "fake-credential",
        "authenticity": 0.99,
        "input_audio_duration": 5.00,
        "net_speech_duration": 4.50,
    }


# server responses with errors

@pytest.fixture(scope="session")
def daspeak_net_speech_duration_error_response():
    return {
        "error": "Voice duration is less than 3 seconds",
        "exception": "VoiceDurationIsNotEnoughException"
    }


# parameters fixtures for daspeak

@pytest.fixture(scope="session")
def daspeak_alive_parameters(mock_option, test_environment, all_environments, daspeak_alive_response):
    ue_sandbox = (f'{eu_sandbox_url}/daspeak/v1/alive', daspeak_alive_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value)
    ue_production = (f'{ue_production_url}/daspeak/v1/alive', daspeak_alive_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value)
    us_sandbox = (f'{us_sandbox_url}/daspeak/v1/alive', daspeak_alive_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value)
    us_production = (f'{us_production_url}/daspeak/v1/alive', daspeak_alive_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value)
    if mock_option:
        alive_parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            ('https://custom-daspeak-url.com/alive', daspeak_alive_response, 200, "https://custom-daspeak-url.com", None, None, None),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == eu_sandobox_test_env:
        alive_parameters = [ue_sandbox]
    elif test_environment == eu_production_test_env:
        alive_parameters = [ue_production]
    elif test_environment == us_sandbox_test_env:
        alive_parameters = [us_sandbox]
    elif test_environment == us_production_test_env:
        alive_parameters = [us_production]
    return alive_parameters


@pytest.fixture(scope="session")
def daspeak_get_models_parameters(mock_option, test_environment, all_environments, daspeak_get_models_response):
    ue_sandbox = (f'{eu_sandbox_url}/daspeak/v1/models', daspeak_get_models_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value)
    ue_production = (f'{ue_production_url}/daspeak/v1/models', daspeak_get_models_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value)
    us_sandbox = (f'{us_sandbox_url}/daspeak/v1/models', daspeak_get_models_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value)
    us_production = (f'{us_production_url}/daspeak/v1/models', daspeak_get_models_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value)
    if mock_option:
        get_models_parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            ('https://custom-daspeak-url.com/models', daspeak_get_models_response, 200, "https://custom-daspeak-url.com", None, None, None),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == eu_sandobox_test_env:
        get_models_parameters = [ue_sandbox]
    elif test_environment == eu_production_test_env:
        get_models_parameters = [ue_production]
    elif test_environment == us_sandbox_test_env:
        get_models_parameters = [us_sandbox]
    elif test_environment == us_production_test_env:
        get_models_parameters = [us_production]
    return get_models_parameters


@pytest.fixture(scope="session")
def daspeak_generate_credential_parameters(mock_option, test_environment, all_environments, daspeak_generate_credential_response):
    ue_sandbox = (f'{eu_sandbox_url}/daspeak/v1/models/fake-model/credential/wav', daspeak_generate_credential_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value)
    ue_production = (f'{ue_production_url}/daspeak/v1/models/fake-model/credential/wav', daspeak_generate_credential_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value)
    us_sandbox = (f'{us_sandbox_url}/daspeak/v1/models/fake-model/credential/wav', daspeak_generate_credential_response, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value)
    us_production = (f'{us_production_url}/daspeak/v1/models/fake-model/credential/wav', daspeak_generate_credential_response, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value)
    if mock_option:
        generate_credential_parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            ('https://custom-daspeak-url.com/models/fake-model/credential/wav', daspeak_generate_credential_response, 200, "https://custom-daspeak-url.com", None, None, None),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == eu_sandobox_test_env:
        generate_credential_parameters = [ue_sandbox]
    elif test_environment == eu_production_test_env:
        generate_credential_parameters = [ue_production]
    elif test_environment == us_sandbox_test_env:
        generate_credential_parameters = [us_sandbox]
    elif test_environment == us_production_test_env:
        generate_credential_parameters = [us_production]
    return generate_credential_parameters


# resources fixtures for daspeak

@pytest.fixture(scope="session")
def audio_file():
    return "tests/daspeak/resources/audio.wav"


@pytest.fixture(scope="session")
def audio_file_bytes():
    with open("tests/daspeak/resources/audio.wav", "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def audio_spoof_file():
    return "tests/daspeak/resources/audio_spoof.wav"


@pytest.fixture(scope="session")
def audio_not_enough_speech_file():
    return "tests/daspeak/resources/audio_not_enough_speech.wav"


@pytest.fixture(scope="session")
def audio_bad_snr_file():
    return "tests/daspeak/resources/audio_bad_snr.wav"


@pytest.fixture(scope="session")
def audio_insufficient_quality_file():
    return "tests/daspeak/resources/audio_insufficient_quality.wav"
