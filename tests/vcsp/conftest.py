import uuid
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from structlog import get_logger
from vericlient import VcspClient
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
    EmptyFileError,
    InvalidAssuranceError,
    InvalidClaimsError,
    RequestValidationError,
)
from vericlient.vcsp.models import (
    DeleteSubjectInput,
    EnrollmentInput,
    EnrollmentOutput,
)

from tests.conftest import provide_testing_parameters

logger = get_logger(__name__)


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


class ResourceTracker:
    """Class to track resources created during tests for cleanup."""

    def __init__(self) -> None:
        self.subject_ids = []

    def add_subject_id(self, subject_id: str) -> None:
        """Add a subject ID to the tracker."""
        if subject_id not in self.subject_ids:
            self.subject_ids.append(subject_id)

    def clear(self) -> None:
        """Clear all tracked resources."""
        self.subject_ids = []


@pytest.fixture(scope="session")
def resource_tracker() -> ResourceTracker:
    """Fixture to track resources for cleanup."""
    return ResourceTracker()


@pytest.fixture()
def temp_subject(vcsp_client, mock_server, resource_tracker, audio_file_path) -> Generator[tuple[str, str], None, None]:
    """Create a temporary subject for testing and clean it up after.

    Returns:
        Generator with a tuple of (subject_id, credential_id)

    """
    if mock_server:
        yield ("mock-subject-id", "mock-credential-id")
        return

    unique_id = str(uuid.uuid4())
    subject_id = f"test-subject-{unique_id}"

    enrollment_data = EnrollmentInput(
        sample=audio_file_path,
        applicant={
            "subject_id": subject_id,
            "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
            "assurance_method_urn": "urn:vcsp:assurance_methods:face:authenticity:v1",
            "assurance": {"authenticity_threshold": 0.5},
        },
    )

    response: EnrollmentOutput = vcsp_client.enroll_subject(data_model=enrollment_data)
    credential_id = response.credential_id

    resource_tracker.add_subject_id(subject_id)

    yield (subject_id, credential_id)


@pytest.fixture(scope="session", autouse=True)
def cleanup_resources(vcsp_client, mock_server, resource_tracker) -> Generator[None, None, None]:   # noqa: PT004
    """Clean up all resources created during tests.

    This fixture runs automatically at the end of the session to clean up all created resources.
    """
    yield

    if mock_server:
        return

    for subject_id in resource_tracker.subject_ids:
        try:
            vcsp_client.delete_account(data_model=DeleteSubjectInput(subject_id=subject_id))
            logger.info("cleaned_up_subject", subject_id=subject_id)
        except Exception as e:   # noqa: PERF203
            logger.exception("failed_to_clean_up_subject", subject_id=subject_id, error=e)

    resource_tracker.clear()


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
                    "type": "number",
                },
            },
            "required": ["authenticity_threshold"],
            "additionalProperties": False,
        },
    }


@pytest.fixture(scope="session")
def vcsp_assurance_method_not_found_error_response():
    return {
        "error": "assurance_method_not_found",
        "title": "Assurance method not found",
        "reason": "Assurance method not found for specified 'assurance_method_urn'",
        "details": {
            "assurance_method_urn": "urn:vcsp:assurance_methods:invalid:method:v1",
        },
    }


@pytest.fixture(scope="session")
def vcsp_enrollment_response():
    return {
        "subject_id": "fake-subject_id",
        "credential_id": "fake-credential_id",
    }


# #################
# # SERVER ERRORS #
# #################

# ### 400 BAD REQUEST ###

@pytest.fixture(scope="session")
def vcsp_empty_file_error_response():
    return {"error": "empty_file", "title": "Empty file", "reason": "Provided file is empty"}


@pytest.fixture(scope="session")
def vcsp_request_validation_error_response():
    return {
        "error": "request_validation",
        "title": "Request validation",
        "reason": "There are one or more errors in the request",
        "details": {
            "details": [
                {
                    "type": "missing",
                    "loc": [
                        "body",
                        "applicant",
                    ],
                    "msg": "Field required",
                    "input": "null",
                },
            ],
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_claims_error_response():
    return {
        "error": "invalid_claims",
        "title": "Invalid claims",
        "reason": "Input claims don't fulfill required schema",
        "details": {
        "input": {},
        "required_schema": {},
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_assurance_error_response():
    return {
        "error": "invalid_assurance",
        "title": "Invalid assurance",
        "reason": "Input assurance doesn't fulfill required schema",
        "details": {
            "input": { },
            "required_schema": {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "title": "Assurance method for face enrollments based on thresholds",
                "type": "object",
                "properties": {
                "authenticity_threshold": {
                "type": "number",
                },
                },
                "required": [
                "authenticity_threshold",
                ],
                "additionalProperties": False,
            },
        },
    }


# ### 404 NOT FOUND ###




# ### 415 UNSUPPORTED MEDIA TYPE ###



# ### 422 UNPROCESSABLE ENTITY ###




# ### 500 INTERNAL SERVER ERROR ###



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
        valid_assurance_method_urn,
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


@pytest.fixture(scope="session")
def vcsp_enrollment_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_enrollment_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/enrollments",
        response=vcsp_enrollment_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_enrollment_exception_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_empty_file_error_response,
        vcsp_request_validation_error_response,
        vcsp_invalid_claims_error_response,
        vcsp_invalid_assurance_error_response,
) -> list[list]:
    response_exceptions = [
        (vcsp_empty_file_error_response, EmptyFileError),
        (vcsp_request_validation_error_response, RequestValidationError),
        (vcsp_invalid_claims_error_response, InvalidClaimsError),
        (vcsp_invalid_assurance_error_response, InvalidAssuranceError),
    ]
    return [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/enrollments",
            response=response,
            status_code=400,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in response_exceptions
    ]
