import pytest

from tests.conftest import provide_testing_parameters


@pytest.fixture(scope="session")
def service_name():
    return "vcsp"


####################
# SERVER RESPONSES #
####################


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
        test_environment, all_environments, mock_option, "vcsp/v1/alive", \
        None, 204, None, service_name,
    )
