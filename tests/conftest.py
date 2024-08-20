import pytest
import requests_mock

from vericlient.environments import Target, Environments, Locations


def pytest_addoption(parser):
    parser.addoption(
        "--mock", action="store_true", default=False, help="Run tests with mock server responses"
    )
    parser.addoption(
        "--env", action="store", default=None, help="Specify the environment to run tests against (e.g., EU_SANDBOX, US_PRODUCTION)"
    )


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
        "EU_SANDBOX",
        "EU_PRODUCTION",
        "US_SANDBOX",
        "US_PRODUCTION",
    ]


@pytest.fixture(scope="session")
def daspeak_alive_parameters(mock_option, test_environment, all_environments):
    ue_sandbox = ('https://api-work.eu.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value)
    ue_production = ('https://api.eu.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value)
    us_sandbox = ('https://api-work.us.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value)
    us_production = ('https://api.us.veri-das.com/daspeak/v1/alive', "", 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value)
    if mock_option:
        alive_parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            ('https://custom-daspeak-url.com/alive', "", 200, "https://custom-daspeak-url.com", None, None, None),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == "EU_SANDBOX":
        alive_parameters = [ue_sandbox]
    elif test_environment == "EU_PRODUCTION":
        alive_parameters = [ue_production]
    elif test_environment == "US_SANDBOX":
        alive_parameters = [us_sandbox]
    elif test_environment == "US_PRODUCTION":
        alive_parameters = [us_production]
    return alive_parameters


@pytest.fixture(scope="session")
def daspeak_get_models_parameters(mock_option, test_environment, all_environments):
    ue_sandbox = ('https://api-work.eu.veri-das.com/daspeak/v1/models', {"version": "", "models": ["model1", "model2"]}, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.EU.value)
    ue_production = ('https://api.eu.veri-das.com/daspeak/v1/models', {"version": "", "models": ["model1", "model2"]}, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.EU.value)
    us_sandbox = ('https://api-work.us.veri-das.com/daspeak/v1/models', {"version": "", "models": ["model1", "model2"]}, 200, None, Target.CLOUD.value, Environments.SANDBOX.value, Locations.US.value)
    us_production = ('https://api.us.veri-das.com/daspeak/v1/models', {"version": "", "models": ["model1", "model2"]}, 200, None, Target.CLOUD.value, Environments.PRODUCTION.value, Locations.US.value)
    if mock_option:
        get_models_parameters = [
            ue_sandbox,
            ue_production,
            us_sandbox,
            us_production,
            ('https://custom-daspeak-url.com/models', {"version": "", "models": ["model1", "model2"]}, 200, "https://custom-daspeak-url.com", None, None, None),
        ]
    elif test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")
    elif test_environment == "EU_SANDBOX":
        get_models_parameters = [ue_sandbox]
    elif test_environment == "EU_PRODUCTION":
        get_models_parameters = [ue_production]
    elif test_environment == "US_SANDBOX":
        get_models_parameters = [us_sandbox]
    elif test_environment == "US_PRODUCTION":
        get_models_parameters = [us_production]
    return get_models_parameters
