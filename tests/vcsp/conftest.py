import uuid
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
from structlog import get_logger
from vericlient import VcspClient
from vericlient.exceptions import ServerError
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
    AssuranceValidationError,
    CredentialConfigurationUrnAlreadyAssignedError,
    EmptyFileError,
    FaceAlignmentError,
    FaceNotFoundError,
    FaceTooSmallError,
    InsufficientQualityError,
    InvalidAssuranceError,
    InvalidAssuranceMethodUrnError,
    InvalidAudioFormatError,
    InvalidClaimsError,
    InvalidCredentialConfigurationUrnError,
    InvalidSnrError,
    InvalidTagsError,
    MoreThanOneFaceError,
    RequestValidationError,
    UnsupportedMediaTypeError,
    VoiceDurationIsNotEnoughError,
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


@pytest.fixture(scope="session")
def test_subject_id():
    return "test-subject-id"


@pytest.fixture(scope="session")
def test_credential_id():
    return "test-credential-id"


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
def vcsp_enrollment_response(test_subject_id):
    return {
        "subject_id": test_subject_id,
        "credential_id": "fake-credential_id",
    }


@pytest.fixture(scope="session")
def vcsp_get_account_response(test_subject_id):
    return {
        "credentials": [
            "497f6eca-6276-4993-bfeb-53cbbbba6f08",
        ],
        "updated_at": "2019-08-24T14:15:22Z",
        "created_at": "2019-08-24T14:15:22Z",
        "subject_id": test_subject_id,
    }


@pytest.fixture(scope="session")
def vcsp_get_all_credentials_response():
    return [
        {
            "sample": {
                "valid_from": "2019-08-24T14:15:22Z",
                "valid_until": "2019-08-24T14:15:22Z",
                "type": "face",
                "content_type": "image/jpg",
                "analysis": {
                    "authenticity_score": 0.9,
                },
            },
            "groups": [
                "employees",
            ],
            "issuer": "Veridas",
            "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
            "updated_at": "2019-08-24T14:15:22Z",
            "created_at": "2019-08-24T14:15:22Z",
            "valid_from": "2019-08-24T14:15:22Z",
            "valid_until": "2019-08-24T14:15:22Z",
            "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
            "tags": [
                "role:employee",
            ],
            "claims": {},
        },
    ]


@pytest.fixture(scope="session")
def vcsp_get_credential_response():
    return {
        "sample": {
            "valid_from": "2019-08-24T14:15:22Z",
            "valid_until": "2019-08-24T14:15:22Z",
            "type": "face",
            "content_type": "image/jpg",
            "analysis": {
            "authenticity_score": 0.9,
            },
        },
        "groups": [
            "employees",
        ],
        "issuer": "Veridas",
        "id": "497f6eca-6276-4993-bfeb-53cbbbba6f08",
        "updated_at": "2019-08-24T14:15:22Z",
        "created_at": "2019-08-24T14:15:22Z",
        "valid_from": "2019-08-24T14:15:22Z",
        "valid_until": "2019-08-24T14:15:22Z",
        "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
        "tags": [
            "role:employee",
        ],
        "claims": {},
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

@pytest.fixture(scope="session")
def vcsp_account_not_found_error_response():
    return {
        "error": "account_not_found",
        "title": "Account not found",
        "reason": "Account not found for specified 'subject_id'",
        "details": {
            "subject_id": "nonexistent_subject_id",
        },
    }


@pytest.fixture(scope="session")
def vcsp_credential_not_found_error_response():
    return {
        "error": "credential_not_found",
        "title": "Credential not found",
        "reason": "Credential not found for specified 'credential_id'",
        "details": {
            "credential_id": "nonexistent_credential_id",
        },
    }


# ### 415 UNSUPPORTED MEDIA TYPE ###

@pytest.fixture(scope="session")
def vcsp_unsupported_media_type_error_response():
    return {
        "error": "unsupported_media_type",
        "title": "Unsupported media type",
        "reason": "Provided file media type is not supported",
        "details": {
            "media_type": "text/plain",
            "allowed_media_types": [
                "image/jpg",
                "image/jpeg",
                "image/png",
            ],
        },
    }


# ### 422 UNPROCESSABLE ENTITY ###

@pytest.fixture(scope="session")
def vcsp_invalid_tags_error_response():
    return {
        "error": "invalid_tags",
        "title": "Invalid tags",
        "reason": "Specified tags don't exist",
        "details": {
            "tag": [
                "invalid_tag",
            ],
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_credential_configuration_urn_error_response():
    return {
        "error": "invalid_credential_configuration_urn",
        "title": "Invalid credential configuration URN",
        "reason": "Specified credential configuration URN does not exist",
        "details": {
            "credential_configuration_urn": "invalid_credential_configuration_urn",
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_assurance_method_urn_error_response():
    return {
        "error": "invalid_assurance_method_urn",
        "title": "Invalid assurance method URN",
        "reason": "Specified assurance method URN does not exist",
        "details": {
            "assurance_method_urn": "invalid_assurance_method_urn",
        },
    }


@pytest.fixture(scope="session")
def vcsp_credential_configuration_already_assigned_error_response():
    return {
        "error": "credential_configuration_urn_already_assigned",
        "title": "Credential configuration URN already assigned",
        "reason": "A credential with specified with specified 'credential_configuration_urn'...",
        "details": {
            "subject_id": "John Doe",
            "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie",
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_audio_format_error_response():
    return {
        "error": "invalid_audio_format",
        "title": "Invalid audio format",
        "reason": "Provided audio contains an unsupported format",
        "details": {
            "msg": "The wav has more channels than are accepted by the system",
        },
    }


@pytest.fixture(scope="session")
def vcsp_invalid_signal_noise_ratio_error_response():
    return {
        "error": "invalid_signal_noise_ratio",
        "title": "Invalid SNR",
        "reason": "Noise level exceeded",
    }


@pytest.fixture(scope="session")
def vcsp_voice_duration_not_enough_error_response():
    return {
        "error": "voice_duration_is_not_enough",
        "title": "Voice duration is not enough",
        "reason": "Voice duration is less than 3 seconds",
    }


@pytest.fixture(scope="session")
def vcsp_insufficient_quality_error_response():
    return {
        "error": "insufficient_quality",
        "title": "Insufficient quality",
        "reason": "The audio quality is not good enough",
    }


@pytest.fixture(scope="session")
def vcsp_face_not_found_error_response():
    return {
        "error": "face_not_found",
        "title": "Face not found",
        "reason": "Face not found in the image",
    }


@pytest.fixture(scope="session")
def vcsp_more_than_one_face_error_response():
    return {
        "error": "more_than_one_face",
        "title": "More than one face",
        "reason": "More than one face detected in the image",
    }


@pytest.fixture(scope="session")
def vcsp_face_too_small_error_response():
    return {
        "error": "face_too_small_for_ias",
        "title": "Face too small for IAS",
        "reason": "Face is too small for IAS",
    }


@pytest.fixture(scope="session")
def vcsp_face_alignment_error_response():
    return {
        "error": "face_alignment",
        "title": "Face alignment",
        "reason": "Face alignment failed",
    }


@pytest.fixture(scope="session")
def vcsp_assurance_validation_error_response():
    return {
        "error": "assurance_validation_error",
        "title": "Assurance validation error",
        "reason": "One or more parameters failed during assurance validation",
        "details": {
            "msg": "Sample authenticity score (0.5) is less than specified authenticity threshold (0.9)",
        },
    }


# ### 500 INTERNAL SERVER ERROR ###

@pytest.fixture(scope="session")
def vcsp_server_error_response():
    return {
        "error": "internal_server_error",
        "title": "Internal server error",
        "reason": "An internal server error occured. Please, contact with your administrator for help",
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
        vcsp_unsupported_media_type_error_response,
        vcsp_invalid_tags_error_response,
        vcsp_invalid_credential_configuration_urn_error_response,
        vcsp_invalid_assurance_method_urn_error_response,
        vcsp_credential_configuration_already_assigned_error_response,
        vcsp_invalid_audio_format_error_response,
        vcsp_invalid_signal_noise_ratio_error_response,
        vcsp_voice_duration_not_enough_error_response,
        vcsp_insufficient_quality_error_response,
        vcsp_face_not_found_error_response,
        vcsp_more_than_one_face_error_response,
        vcsp_face_too_small_error_response,
        vcsp_face_alignment_error_response,
        vcsp_assurance_validation_error_response,
        vcsp_server_error_response,
) -> list[list]:
    four_hundred_responses = [
        (vcsp_empty_file_error_response, EmptyFileError),
        (vcsp_request_validation_error_response, RequestValidationError),
        (vcsp_invalid_claims_error_response, InvalidClaimsError),
        (vcsp_invalid_assurance_error_response, InvalidAssuranceError),
    ]
    four_hundred_responses = [
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
        for response, exception in four_hundred_responses
    ]
    unsupported_media_type_response = [provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/enrollments",
        response=vcsp_unsupported_media_type_error_response,
        status_code=415,
        exception=UnsupportedMediaTypeError,
        service_name=service_name,
    )]
    four_hundred_twenty_two_responses = [
        (vcsp_invalid_tags_error_response, InvalidTagsError),
        (vcsp_invalid_credential_configuration_urn_error_response, InvalidCredentialConfigurationUrnError),
        (vcsp_invalid_assurance_method_urn_error_response, InvalidAssuranceMethodUrnError),
        (vcsp_credential_configuration_already_assigned_error_response, CredentialConfigurationUrnAlreadyAssignedError),
        (vcsp_invalid_audio_format_error_response, InvalidAudioFormatError),
        (vcsp_invalid_signal_noise_ratio_error_response, InvalidSnrError),
        (vcsp_voice_duration_not_enough_error_response, VoiceDurationIsNotEnoughError),
        (vcsp_insufficient_quality_error_response, InsufficientQualityError),
        (vcsp_face_not_found_error_response, FaceNotFoundError),
        (vcsp_more_than_one_face_error_response, MoreThanOneFaceError),
        (vcsp_face_too_small_error_response, FaceTooSmallError),
        (vcsp_face_alignment_error_response, FaceAlignmentError),
        (vcsp_assurance_validation_error_response, AssuranceValidationError),
    ]
    four_hundred_twenty_two_responses = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/enrollments",
            response=response,
            status_code=422,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_twenty_two_responses
    ]
    server_error_response = [provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/enrollments",
        response=vcsp_server_error_response,
        status_code=500,
        exception=ServerError,
        service_name=service_name,
    )]
    return four_hundred_responses + unsupported_media_type_response + four_hundred_twenty_two_responses + server_error_response


@pytest.fixture(scope="session")
def vcsp_get_account_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_get_account_response,
        test_subject_id,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/accounts/{test_subject_id}",
        response=vcsp_get_account_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_account_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        test_subject_id,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/accounts/{test_subject_id}",
        response={},
        status_code=204,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_get_all_credentials_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_get_all_credentials_response,
        test_subject_id,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/accounts/{test_subject_id}/credentials",
        response=vcsp_get_all_credentials_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_get_credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        vcsp_get_credential_response,
        test_subject_id,
        test_credential_id,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/accounts/{test_subject_id}/credentials/{test_credential_id}",
        response=vcsp_get_credential_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_credential_parameters(
        mock_option,
        test_environment,
        all_environments,
        service_name,
        test_subject_id,
        test_credential_id,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/accounts/{test_subject_id}/credentials/{test_credential_id}",
        response={},
        status_code=204,
        exception=None,
        service_name=service_name,
    )
