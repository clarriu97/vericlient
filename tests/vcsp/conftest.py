from unittest.mock import MagicMock

import pytest

from vericlient import VcspClient
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)

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


@pytest.fixture(scope="session")
def vcsp_credential_configurations_response():
    return [
        "urn:vcsp:credential_configurations:face:selfie:v1",
        "urn:vcsp:credential_configurations:face:selfie:v2",
    ]


@pytest.fixture(scope="session")
def valid_assurance_method_urn():
    return "urn:vcsp:assurance_methods:voice:authenticity:v1"


@pytest.fixture(scope="session")
def vcsp_assurance_methods_response():
    return [
        "urn:vcsp:assurance_methods:face:authenticity:v1",
        "urn:vcsp:assurance_methods:face:authenticity:v2",
    ]


@pytest.fixture(scope="session")
def vcsp_assurance_method_response(valid_assurance_method_urn):
    return {
        "urn": valid_assurance_method_urn,
        "schema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Assurance method for face enrollments based on thresholds",
            "type": "object",
            "properties": {
                "authenticity_threshold": {
                    "type": "number"
                }
            },
            "required": ["authenticity_threshold"],
            "additionalProperties": False
        }
    }


@pytest.fixture(scope="session")
def vcsp_assurance_method_not_found_error_response():
    return {
        "error": "assurance_method_not_found",
        "title": "Assurance method not found",
        "reason": "Assurance method not found for specified 'assurance_method_urn'",
        "details": {
            "assurance_method_urn": "urn:vcsp:assurance_methods:invalid:method:v1"
        }
    }

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


@pytest.fixture(scope="session")
def vcsp_credential_configuration_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_credential_configurations_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/credential_configurations",
        response=vcsp_credential_configurations_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_assurance_methods_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_assurance_methods_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/assurance_methods",
        response=vcsp_assurance_methods_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_assurance_method_info_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_assurance_method_response,
        valid_assurance_method_urn
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/assurance_methods/{valid_assurance_method_urn}",
        response=vcsp_assurance_method_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_assurance_method_not_found_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_assurance_method_not_found_error_response,
) -> list:
    invalid_assurance_method_urn = "urn:vcsp:assurance_methods:invalid:method:v1"
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/assurance_methods/{invalid_assurance_method_urn}",
        response=vcsp_assurance_method_not_found_error_response,
        status_code=404,
        exception=AssuranceMethodNotFoundError,
        service_name=service_name,
    )
