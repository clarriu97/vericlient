import contextlib
import uuid
from collections.abc import Callable, Generator
from unittest.mock import MagicMock

import pytest
from structlog import get_logger

from tests.conftest import provide_testing_parameters
from vericlient import VcspClient
from vericlient.environments import Environments, Locations
from vericlient.exceptions import ServerError
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
    AssuranceValidationError,
    CredentialConfigurationUrnAlreadyAssignedError,
    EmptyFileError,
    EnrollmentsLimitExceededError,
    FaceAlignmentError,
    FaceNotFoundError,
    FaceTooSmallError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
    GroupsLimitExceededError,
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
    TagAlreadyExistsError,
    TagListEmptyError,
    TagsLimitExceededError,
    UnsupportedMediaTypeError,
    VoiceDurationIsNotEnoughError,
)
from vericlient.vcsp.models import (
    Applicant,
)

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

    # The client validates these against the enum values, which are lowercase.
    env_mapping = {
        "EU_SANDBOX": (Environments.SANDBOX.value, Locations.EU.value),
        "EU_PRODUCTION": (Environments.PRODUCTION.value, Locations.EU.value),
        "US_SANDBOX": (Environments.SANDBOX.value, Locations.US.value),
        "US_PRODUCTION": (Environments.PRODUCTION.value, Locations.US.value),
    }

    environment, location = env_mapping.get(test_environment)

    return VcspClient(
        environment=environment,
        location=location,
    )


# ---------------------------------------------------------------------------
# Repeatable tests against a stateful service
#
# VCSP keeps state: enrolling a subject, creating a group or a tag all write to a database
# that outlives the test. Everything created here is therefore named with a recognisable
# prefix, torn down by the fixture that created it, and swept at the start and end of the
# session in case a previous run died before its teardown.
#
# Each kind has its own naming rule, enforced by the API:
#   subjects  free-form                       -> vericlient-test-<uuid>
#   groups    ^[a-zA-Z_][a-zA-Z0-9_]{2,63}$   -> vericlient_test_<hex>
#   tags      ^[a-zA-Z0-9]+:[a-zA-Z0-9]+$     -> vericlient:test
# ---------------------------------------------------------------------------

SUBJECT_PREFIX = "vericlient-test"
GROUP_PREFIX = "vericlient_test"
TEST_TAG = "vericlient:test"

SANDBOX_ENVIRONMENTS = ("EU_SANDBOX", "US_SANDBOX")

# The subscription caps groups, and the shared sandbox already holds most of them, so tests
# that create groups have to be few and clean up immediately.
GROUPS_LIMIT = 10


def unique_subject_id() -> str:
    """Return a subject id no other run will collide with."""
    return f"{SUBJECT_PREFIX}-{uuid.uuid4()}"


def unique_group_name() -> str:
    """Return a group name that satisfies the API's pattern and no other run will collide with."""
    return f"{GROUP_PREFIX}_{uuid.uuid4().hex[:12]}"


def unique_tag() -> str:
    r"""Return a tag no other run will collide with.

    The service's pattern is `^\w{1,32}:\w{1,32}$`, so neither half may hold a hyphen.
    """
    return f"vericlient:{uuid.uuid4().hex[:12]}"


class ResourceTracker:
    """Records what a test created so it can be undone in reverse order.

    Reverse order matters: a credential has to go before the group it belongs to.
    """

    def __init__(self) -> None:
        self._entries: list[tuple[str, str, Callable[[], None]]] = []

    def add(self, kind: str, identifier: str, delete: Callable[[], None]) -> None:
        """Record a resource and how to remove it."""
        self._entries.append((kind, identifier, delete))

    def forget(self, identifier: str) -> None:
        """Drop a resource the test deleted itself, so teardown does not try again."""
        self._entries = [e for e in self._entries if e[1] != identifier]

    def cleanup(self) -> list[str]:
        """Delete everything recorded, newest first. Returns whatever could not be deleted."""
        failures = []
        for kind, identifier, delete in reversed(self._entries):
            try:
                delete()
                logger.info("cleaned_up", kind=kind, identifier=identifier)
            except Exception as error:  # noqa: BLE001 - teardown reports, it does not raise
                failures.append(f"{kind} {identifier}: {error}")
                logger.warning("cleanup_failed", kind=kind, identifier=identifier, error=str(error))
        self._entries = []
        return failures


@pytest.fixture(scope="session")
def writes_allowed(mock_server, test_environment) -> bool:
    """Whether this run may create resources on the server.

    Against a mock, anything goes. Against real infrastructure, only sandbox: these tests
    create and delete data, and `pdm run test-eu-production` exists.
    """
    if mock_server:
        return True
    return test_environment in SANDBOX_ENVIRONMENTS


@pytest.fixture
def real_writes(vcsp_client, mock_server, writes_allowed):
    """Skip a test that needs to create real resources when it must not."""
    if mock_server:
        pytest.skip("This test exercises real infrastructure")
    if not writes_allowed:
        pytest.skip("Tests that create resources only run against a sandbox environment")
    return vcsp_client


@pytest.fixture
def resource_tracker(keep_resources) -> Generator[ResourceTracker, None, None]:
    """Track resources for one test and remove them when it ends."""
    tracker = ResourceTracker()
    yield tracker
    if keep_resources:
        logger.warning("keeping_resources", reason="--keep-resources")
        return
    failures = tracker.cleanup()
    if failures:
        pytest.fail("could not clean up: " + "; ".join(failures))


@pytest.fixture
def temp_tag(real_writes, resource_tracker) -> str:
    """Create the shared test tag and remove it afterwards."""
    real_writes.create_tags(tags=[TEST_TAG])
    resource_tracker.add("tag", TEST_TAG, lambda: real_writes.delete_tag(name=TEST_TAG))
    return TEST_TAG


@pytest.fixture
def own_tag(real_writes, resource_tracker) -> str:
    """Create a tag of this test's own and remove it afterwards.

    Unlike `temp_tag`, which owns the shared `vericlient:test`, this one collides with
    nothing — including the session-scoped fixture that keeps the shared tag alive.
    """
    name = unique_tag()
    real_writes.create_tags(tags=[name])
    resource_tracker.add("tag", name, lambda: real_writes.delete_tag(name=name))
    return name


@pytest.fixture
def temp_group(real_writes, resource_tracker, voice_credential_configuration) -> str:
    """Create a group and remove it afterwards."""
    name = unique_group_name()
    real_writes.create_group(
        name=name,
        credential_configuration_urn=voice_credential_configuration,
    )
    resource_tracker.add("group", name, lambda: real_writes.delete_group(name=name))
    return name


@pytest.fixture(scope="session")
def voice_credential_configuration(vcsp_client, mock_server) -> str:
    """Return a voice credential configuration this subscription actually offers.

    Read from the service rather than hardcoded: the URNs differ between subscriptions.
    """
    if mock_server:
        return "urn:vcsp:credential_configurations:voice_telephone:v1"
    configurations = vcsp_client.get_credential_configurations().credential_configurations
    return next(c for c in configurations if "voice" in c)


@pytest.fixture(scope="session")
def face_credential_configuration(vcsp_client, mock_server) -> str:
    """Return a face credential configuration this subscription actually offers.

    The face pipeline rejects a photo on grounds the voice one has no equivalent of, so the
    error tests need an enrolment that reads a face.
    """
    if mock_server:
        return "urn:vcsp:credential_configurations:face_selfie:v1"
    configurations = vcsp_client.get_credential_configurations().credential_configurations
    return next(c for c in configurations if "face" in c)


@pytest.fixture
def real_vcsp(vcsp_client, mock_server):
    """Skip a test that only makes sense against the real service and creates nothing.

    Separate from `real_writes`: a read-only check is safe against production too, so it does
    not need the sandbox guard.
    """
    if mock_server:
        pytest.skip("This test exercises real infrastructure")
    return vcsp_client


@pytest.fixture(scope="session")
def enrollment_assurance_method(vcsp_client, mock_server) -> str:
    """Return an enrollment assurance method this subscription actually offers."""
    if mock_server:
        return "urn:vcsp:assurance_methods:enrollment:authenticity_threshold:v1"
    methods = vcsp_client.get_assurance_methods().assurance_methods
    return next(m for m in methods if "enrollment:authenticity_threshold" in m)


@pytest.fixture(scope="session")
def matching_assurance_method(vcsp_client, mock_server) -> str:
    """Return a matching assurance method this subscription actually offers."""
    if mock_server:
        return "urn:vcsp:assurance_methods:matching:biometric_threshold:v1"
    methods = vcsp_client.get_assurance_methods().assurance_methods
    return next(m for m in methods if "matching:biometric_threshold" in m)


@pytest.fixture(scope="session")
def clustering_assurance_method(vcsp_client, mock_server) -> str:
    """Return a clustering assurance method this subscription actually offers."""
    if mock_server:
        return "urn:vcsp:assurance_methods:clustering:thresholds:v1"
    methods = vcsp_client.get_assurance_methods().assurance_methods
    return next(m for m in methods if "clustering" in m)


@pytest.fixture
def temp_subject(
    real_writes,
    resource_tracker,
    shared_test_tag,
    audio_file_path,
    voice_credential_configuration,
    enrollment_assurance_method,
) -> tuple[str, str]:
    """Enrol a subject and remove its account afterwards.

    Deleting the account removes its credentials too, so one entry covers both.
    """
    subject_id = unique_subject_id()
    enrollment = real_writes.enroll_subject(
        sample=audio_file_path,
        applicant=Applicant(
            subject_id=subject_id,
            credential_configuration_urn=voice_credential_configuration,
            assurance_method_urn=enrollment_assurance_method,
            assurance={"authenticity_threshold": 0.5},
            # Tagging is what lets the sweeper find this account if teardown never runs.
            tags=[shared_test_tag],
        ),
    )
    resource_tracker.add(
        "account",
        subject_id,
        lambda: real_writes.delete_account(subject_id=subject_id),
    )
    return subject_id, enrollment.credential_id


@pytest.fixture(scope="session")
def shared_test_tag(vcsp_client, mock_server, writes_allowed) -> str:
    """Make sure the tag that marks test credentials exists.

    A credential can only carry a tag the service already knows about, so this runs once per
    session. The sweeper removes it at the end.
    """
    if not mock_server and writes_allowed:
        with contextlib.suppress(Exception):
            vcsp_client.create_tags(tags=[TEST_TAG])
    return TEST_TAG


@pytest.fixture(scope="session", autouse=True)
def sweep_leftovers(vcsp_client, mock_server, writes_allowed, keep_resources) -> Generator[None, None, None]:
    """Remove anything a previous run left behind, before and after this one.

    Per-test teardown does not survive a crash, so this is what actually makes the suite
    repeatable. It only ever touches resources carrying the test prefixes, because the
    sandbox is shared with real subscriptions.

    Accounts are found through the test tag. The deployment holds far too many credentials
    to walk, but filtering by tag narrows it to the ones this suite created.
    """

    def sweep(when: str) -> None:
        if mock_server or not writes_allowed or keep_resources:
            return

        with contextlib.suppress(Exception):
            leaked = vcsp_client.list_credentials(tags=[TEST_TAG]).items
            for subject_id in {credential.subject_id for credential in leaked}:
                with contextlib.suppress(Exception):
                    vcsp_client.delete_account(subject_id=subject_id)
                    logger.info("swept_account", subject_id=subject_id, when=when)

        for group in vcsp_client.get_groups().items:
            if group.name.startswith(GROUP_PREFIX):
                with contextlib.suppress(Exception):
                    vcsp_client.delete_group(name=group.name)
                    logger.info("swept_group", name=group.name, when=when)

        for tag in vcsp_client.get_tags().items:
            if tag.name == TEST_TAG:
                with contextlib.suppress(Exception):
                    vcsp_client.delete_tag(name=tag.name)
                    logger.info("swept_tag", name=tag.name, when=when)

        # Tasks are deliberately not swept. They carry no name to recognise ours by, the
        # listing is subscription-wide, and deleting someone else's would be worse than
        # leaving one behind. A leaked task expires on its own after thirty days; the tests
        # that create one delete it in their own teardown.

    sweep("before")
    yield
    sweep("after")


@pytest.fixture(scope="session")
def test_subject_id():
    return "test-subject-id"


@pytest.fixture(scope="session")
def test_credential_id():
    return "test-credential-id"


@pytest.fixture(scope="session")
def test_tag_name():
    return "test:tag1"


@pytest.fixture(scope="session")
def test_tag_name_2():
    return "test:tag2"


@pytest.fixture(scope="session")
def test_group_name():
    return "test:group"


@pytest.fixture(scope="session")
def test_group_name_2():
    return "test:group2"


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


@pytest.fixture(scope="session")
def vcsp_create_tags_response(test_tag_name, test_tag_name_2):
    return {
        "tags": [
            test_tag_name,
            test_tag_name_2,
        ],
        "created_at": "2019-08-24T14:15:22Z",
    }


@pytest.fixture(scope="session")
def vcsp_get_tags_response(test_tag_name, test_tag_name_2):
    return {
        "items": [
            {
                "name": test_tag_name,
                "created_at": "2019-08-24T14:15:22Z",
            },
            {
                "name": test_tag_name_2,
                "created_at": "2019-08-24T14:15:22Z",
            },
        ],
        "total": 2,
        "page": 1,
        "size": 100,
        "pages": 1,
    }


@pytest.fixture(scope="session")
def vcsp_create_group_response(test_group_name):
    return {
        "name": test_group_name,
        "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
        "size": 0,
        "created_at": "2019-08-24T14:15:22Z",
        "description": "test:group",
        "expired_at": "2019-08-24T14:15:22Z",
        "updated_at": "2019-08-24T14:15:22Z",
    }


@pytest.fixture(scope="session")
def vcsp_get_groups_response(test_group_name, test_group_name_2):
    return {
        "items": [
            {
                "name": test_group_name,
                "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
                "size": 0,
                "created_at": "2019-08-24T14:15:22Z",
                "description": test_group_name,
                "expired_at": "2019-08-24T14:15:22Z",
                "updated_at": "2019-08-24T14:15:22Z",
            },
            {
                "name": test_group_name_2,
                "credential_configuration_urn": "urn:vcsp:credential_configurations:face:selfie:v1",
                "size": 0,
                "created_at": "2019-08-24T14:15:22Z",
                "description": test_group_name_2,
                "expired_at": "2019-08-24T14:15:22Z",
                "updated_at": "2019-08-24T14:15:22Z",
            },
        ],
        "total": 2,
        "page": 1,
        "size": 100,
        "pages": 1,
    }


@pytest.fixture(scope="session")
def vcsp_get_group_response(vcsp_create_group_response):
    return vcsp_create_group_response


@pytest.fixture(scope="session")
def vcsp_get_group_members_response():
    return {
        "items": [
            {
                "subject_id": "test:subject",
                "credential_id": "test:credential",
                "expired_in_group": "2019-08-24T14:15:22Z",
                "claims": {},
                "tags": [],
            },
            {
                "subject_id": "test:subject2",
                "credential_id": "test:credential2",
                "expired_in_group": "2019-08-24T14:15:22Z",
                "claims": {},
                "tags": [],
            },
        ],
        "total": 2,
        "page": 1,
        "size": 100,
        "pages": 1,
    }


#################
# SERVER ERRORS #
#################

### 400 BAD REQUEST ###


@pytest.fixture(scope="session")
def vcsp_empty_file_error_response():
    return {"error": "empty_file", "title": "Empty file", "reason": "Provided file is empty"}


@pytest.fixture(scope="session")
def vcsp_request_validation_error_response():
    return {
        "error": "request_validation_error",
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
            "input": {},
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


### 403 FORBIDDEN ###


@pytest.fixture(scope="session")
def vcsp_enrollments_limit_exceeded_error_response():
    return {
        "error": "enrollments_limit_exceeded",
        "title": "Enrollments limit exceeded",
        "reason": "Enrollments limit has been exceeded",
        "details": {
            "enrollments_limit": 10,
        },
    }


@pytest.fixture(scope="session")
def vcsp_tags_limit_exceeded_error_response():
    return {
        "error": "tags_limit_exceeded",
        "title": "Tags limit exceeded",
        "reason": "Tags limit has been exceeded",
        "details": {
            "tags_limit": 10,
        },
    }


@pytest.fixture(scope="session")
def vcsp_tags_already_exist_error_response():
    return {
        "error": "tags_already_exist",
        "title": "Tags already exist",
        "reason": "One or more tags already exist",
        "details": {
            "tags": ["existing_tag1", "existing_tag2"],
        },
    }


@pytest.fixture(scope="session")
def vcsp_tag_list_empty_error_response():
    return {
        "error": "tag_list_empty",
        "title": "Tag list empty",
        "reason": "Tag list cannot be empty",
        "details": {},
    }


@pytest.fixture(scope="session")
def vcsp_groups_limit_exceeded_error_response():
    return {
        "error": "groups_limit_exceeded",
        "title": "Groups limit exceeded",
        "reason": "Groups limit has been exceeded",
        "details": {
            "groups_limit": 10,
        },
    }


### 404 NOT FOUND ###


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


### 415 UNSUPPORTED MEDIA TYPE ###


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


### 422 UNPROCESSABLE ENTITY ###


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
def vcsp_group_already_exists_error_response():
    return {
        "error": "group_already_exists",
        "title": "Group already exists",
        "reason": "A group with specified name does already exist",
        "details": {
            "name": "employees",
        },
    }


@pytest.fixture(scope="session")
def vcsp_group_not_found_error_response():
    return {
        "error": "group_not_found",
        "title": "Group not found",
        "reason": "Group not found for specified 'group_name'",
        "details": {
            "group_name": "nonexistent_group_name",
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


### 500 INTERNAL SERVER ERROR ###


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
    vcsp_enrollments_limit_exceeded_error_response,
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
    four_hundred_three_response = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/enrollments",
            response=vcsp_enrollments_limit_exceeded_error_response,
            status_code=403,
            exception=EnrollmentsLimitExceededError,
            service_name=service_name,
        )
    ]
    unsupported_media_type_response = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/enrollments",
            response=vcsp_unsupported_media_type_error_response,
            status_code=415,
            exception=UnsupportedMediaTypeError,
            service_name=service_name,
        )
    ]
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
    server_error_response = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/enrollments",
            response=vcsp_server_error_response,
            status_code=500,
            exception=ServerError,
            service_name=service_name,
        )
    ]
    return (
        four_hundred_responses
        + four_hundred_three_response
        + unsupported_media_type_response
        + four_hundred_twenty_two_responses
        + server_error_response
    )


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


@pytest.fixture(scope="session")
def vcsp_create_tags_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_create_tags_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/tags",
        response=vcsp_create_tags_response,
        status_code=201,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_create_tags_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_request_validation_error_response,
    vcsp_tags_limit_exceeded_error_response,
    vcsp_tags_already_exist_error_response,
    vcsp_tag_list_empty_error_response,
) -> list[list]:
    four_hundred_responses = [
        (vcsp_request_validation_error_response, RequestValidationError),
    ]
    four_hundred_responses = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/tags",
            response=response,
            status_code=400,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_responses
    ]
    four_hundred_three_response = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/tags",
            response=vcsp_tags_limit_exceeded_error_response,
            status_code=403,
            exception=TagsLimitExceededError,
            service_name=service_name,
        )
    ]
    four_hundred_twenty_two_responses = [
        (vcsp_tags_already_exist_error_response, TagAlreadyExistsError),
        (vcsp_tag_list_empty_error_response, TagListEmptyError),
    ]
    four_hundred_twenty_two_responses = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/tags",
            response=response,
            status_code=422,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_twenty_two_responses
    ]
    return four_hundred_responses + four_hundred_three_response + four_hundred_twenty_two_responses


@pytest.fixture(scope="session")
def vcsp_get_tags_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_get_tags_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/tags",
        response=vcsp_get_tags_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_tag_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    test_tag_name,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/tags/{test_tag_name}",
        response={},
        status_code=204,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_tag_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_invalid_tags_error_response,
) -> list[list]:
    four_hundred_twenty_two_responses = [
        (vcsp_invalid_tags_error_response, InvalidTagsError),
    ]
    return [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/tags/invalid_tag",
            response=response,
            status_code=422,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_twenty_two_responses
    ]


@pytest.fixture(scope="session")
def vcsp_create_group_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_create_group_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/groups",
        response=vcsp_create_group_response,
        status_code=201,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_create_group_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_request_validation_error_response,
    vcsp_groups_limit_exceeded_error_response,
    vcsp_invalid_credential_configuration_urn_error_response,
    vcsp_group_already_exists_error_response,
) -> list[list]:
    four_hundred_responses = [
        (vcsp_request_validation_error_response, RequestValidationError),
    ]
    four_hundred_responses = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups",
            response=response,
            status_code=400,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_responses
    ]
    four_hundred_three_response = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups",
            response=vcsp_groups_limit_exceeded_error_response,
            status_code=403,
            exception=GroupsLimitExceededError,
            service_name=service_name,
        )
    ]
    four_hundred_twenty_two_responses = [
        (vcsp_invalid_credential_configuration_urn_error_response, InvalidCredentialConfigurationUrnError),
        (vcsp_group_already_exists_error_response, GroupAlreadyExistsError),
    ]
    four_hundred_twenty_two_responses = [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups",
            response=response,
            status_code=422,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_twenty_two_responses
    ]
    return four_hundred_responses + four_hundred_three_response + four_hundred_twenty_two_responses


@pytest.fixture(scope="session")
def vcsp_get_groups_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_get_groups_response,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint="vcsp/v1/groups",
        response=vcsp_get_groups_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_get_group_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_group_not_found_error_response,
) -> list[list]:
    four_hundred_four_responses = [
        (vcsp_group_not_found_error_response, GroupNotFoundError),
    ]
    return [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups/nonexistent_group_name",
            response=response,
            status_code=404,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_four_responses
    ]


@pytest.fixture(scope="session")
def vcsp_get_group_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_get_group_response,
    test_group_name,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/groups/{test_group_name}",
        response=vcsp_get_group_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_group_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    test_group_name,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/groups/{test_group_name}",
        response={},
        status_code=204,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_delete_group_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_group_not_found_error_response,
) -> list[list]:
    four_hundred_four_responses = [
        (vcsp_group_not_found_error_response, GroupNotFoundError),
    ]
    return [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups/nonexistent_group_name",
            response=response,
            status_code=404,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_four_responses
    ]


@pytest.fixture(scope="session")
def vcsp_get_group_members_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_get_group_members_response,
    test_group_name,
) -> list:
    return provide_testing_parameters(
        test_environment=test_environment,
        all_environments=all_environments,
        mock_option=mock_option,
        endpoint=f"vcsp/v1/groups/{test_group_name}/credentials",
        response=vcsp_get_group_members_response,
        status_code=200,
        exception=None,
        service_name=service_name,
    )


@pytest.fixture(scope="session")
def vcsp_get_group_members_exception_parameters(
    mock_option,
    test_environment,
    all_environments,
    service_name,
    vcsp_group_not_found_error_response,
) -> list[list]:
    four_hundred_four_responses = [
        (vcsp_group_not_found_error_response, GroupNotFoundError),
    ]
    return [
        provide_testing_parameters(
            test_environment=test_environment,
            all_environments=all_environments,
            mock_option=mock_option,
            endpoint="vcsp/v1/groups/nonexistent_group_name/credentials",
            response=response,
            status_code=404,
            exception=exception,
            service_name=service_name,
        )
        for response, exception in four_hundred_four_responses
    ]
