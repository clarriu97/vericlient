from unittest.mock import MagicMock

import pytest
from vericlient import VcspClient

from tests.conftest import provide_testing_parameters


@pytest.fixture(scope="session")
def service_name():
    return "vcsp"


@pytest.fixture(scope="session")
def vcsp_client(mock_server, test_environment, all_environments) -> VcspClient:
    """Create a VCSP client for testing.

    This fixture creates a client that can be used for all VCSP tests.
    """
    if mock_server:
        return VcspClient(apikey="fake-apikey")

    if test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")

    env_mapping = {
        "EU_SANDBOX": ("SANDBOX", "EU"),
        "EU_PRODUCTION": ("PRODUCTION", "EU"),
        "US_SANDBOX": ("SANDBOX", "US"),
        "US_PRODUCTION": ("PRODUCTION", "US"),
    }

    environment, location = env_mapping.get(test_environment)

    return VcspClient(
        environment=environment,
        location=location,
    )


####################
# SERVER RESPONSES #
####################

@pytest.fixture(scope="session")
def vcsp_alive_response():
    response = MagicMock()
    response.status_code = 204
    return response


#################
# SERVER ERRORS #
#################


#######################
# PARAMETERS FIXTURES #
#######################

@pytest.fixture(scope="session")
def vcsp_alive_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
    ) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/alive",
        response=None,
        status_code=204,
        exception=None,
        service_name=service_name,
    )
