import pytest
import requests_mock
from vericlient.environments import Environments, Locations

# pytest hooks

def pytest_addoption(parser):
    parser.addoption(
        "--mock", action="store_true", default=False, help="Run tests with mock server responses",
    )
    parser.addoption(
        "--env", action="store", default=None, help=\
            "Specify the environment to run tests against (e.g., EU_SANDBOX, US_PRODUCTION)",
    )


# variables

eu_sandbox_url = "https://api-work.eu.veri-das.com"
ue_production_url = "https://api.eu.veri-das.com"
us_sandbox_url = "https://api-work.us.veri-das.com"
us_production_url = "https://api.us.veri-das.com"

eu_sandobox_test_env = "EU_SANDBOX"
eu_production_test_env = "EU_PRODUCTION"
us_sandbox_test_env = "US_SANDBOX"
us_production_test_env = "US_PRODUCTION"


# general fixtures

@pytest.fixture(scope="session")
def mock_option(request):
    return request.config.getoption("--mock")


@pytest.fixture(scope="session")
def test_environment(request):
    return request.config.getoption("--env")


@pytest.fixture(scope="session")
def mock_server(mock_option, test_environment):
    if mock_option:
        with requests_mock.Mocker() as m:
            yield m
    else:
        if not test_environment:
            pytest.fail("No environment specified for real tests. Use --env to specify one.")
        yield None


@pytest.fixture(scope="session")
def all_environments():
    return [
        eu_sandobox_test_env,
        eu_production_test_env,
        us_sandbox_test_env,
        us_production_test_env,
    ]


def provide_testing_parameters(
        test_environment: str,
        all_environments: list,
        mock_option: bool,      # noqa: FBT001
        endpoint: str,
        response: dict,
        status_code: int,
        exception: Exception,
        service_name: str,
    ) -> list:
    """Provide the parameters necessary for service testing depending on the test environment.

    Those parameters are:
    - endpoint: the endpoint to test
    - response: the response to return
    - status_code: the status code to return
    - exception: the exception to raise if any
    - service_name: the name of the service to test

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
            (f"https://custom-{service_name}-url.com/{endpoint}", response, status_code, \
                f"https://custom-{service_name}-url.com/{service_name}/v1", None, None, exception),
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

