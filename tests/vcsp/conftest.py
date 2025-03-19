import pytest

from unittest.mock import MagicMock

from tests.conftest import provide_testing_parameters


@pytest.fixture(scope="session")
def service_name():
    return "vcsp"


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
