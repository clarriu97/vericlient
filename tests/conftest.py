import pytest
import requests_mock

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
