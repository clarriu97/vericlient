import pytest
import requests_mock


def pytest_addoption(parser):
    parser.addoption(
        "--mock", action="store_true", default=False, help="Run tests with mock server responses"
    )


@pytest.fixture(scope="session")
def mock_option(request):
    return request.config.getoption("--mock")


@pytest.fixture(scope="session")
def mock_server(mock_option):
    if mock_option:
        with requests_mock.Mocker() as m:
            yield m
    else:
        yield None
