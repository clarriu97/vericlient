import pytest

from vericlient import DasfaceClient
from vericlient.environments import Environments, Locations

SANDBOX_ENVIRONMENTS = ("EU_SANDBOX", "US_SANDBOX")


@pytest.fixture(scope="session")
def service_name():
    return "dasface"


@pytest.fixture(scope="session")
def dasface_client(mock_server, test_environment, all_environments) -> DasfaceClient:
    """Create a das-Face client for testing."""
    if mock_server:
        return DasfaceClient(apikey="fake-apikey")

    if test_environment not in all_environments:
        pytest.fail(f"Invalid environment specified. Use one of {all_environments}")

    # The client validates these against the enum values, which are lowercase.
    env_mapping = {
        "EU_SANDBOX": (Environments.SANDBOX.value, Locations.EU.value),
        "EU_PRODUCTION": (Environments.PRODUCTION.value, Locations.EU.value),
        "US_SANDBOX": (Environments.SANDBOX.value, Locations.US.value),
        "US_PRODUCTION": (Environments.PRODUCTION.value, Locations.US.value),
    }
    environment, location = env_mapping[test_environment]
    return DasfaceClient(environment=environment, location=location)


@pytest.fixture
def real_dasface(dasface_client, mock_server):
    """Skip a test that only makes sense against the real service.

    das-Face creates nothing that outlives a request — no accounts, no groups — so unlike
    VCSP there is no state to clean up and no sandbox-only guard to enforce.
    """
    if mock_server:
        pytest.skip("This test exercises real infrastructure")
    return dasface_client


####################
# RESOURCE FIXTURES #
####################


@pytest.fixture(scope="session")
def face_image_path() -> str:
    return "tests/dasface/resources/face.jpg"


@pytest.fixture(scope="session")
def face_image(face_image_path) -> bytes:
    with open(face_image_path, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def other_face_image_path() -> str:
    """Return a different person, small enough that the authenticity analysis rejects it."""
    return "tests/dasface/resources/other_face.png"


@pytest.fixture(scope="session")
def other_face_image(other_face_image_path) -> bytes:
    with open(other_face_image_path, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def face_video_path() -> str:
    return "tests/dasface/resources/face_video.mp4"


@pytest.fixture(scope="session")
def face_video(face_video_path) -> bytes:
    with open(face_video_path, "rb") as f:
        return f.read()


####################
# SERVER RESPONSES #
####################


@pytest.fixture(scope="session")
def dasface_models_response():
    return [
        {
            "tag": "20240523",
            "hash": "fake-hash",
            "mode": "default-mode",
            "methods": ["Face"],
            "length": 128,
        },
        {
            "tag": "20240523",
            "hash": "fake-hash",
            "mode": "document-mode",
            "methods": ["Face"],
            "length": 128,
        },
    ]


@pytest.fixture(scope="session")
def dasface_credential_response():
    return {
        "credential": "fake-credential",
        "model": {"hash": "fake-hash", "mode": "default-mode"},
    }


@pytest.fixture(scope="session")
def dasface_metadata_response():
    return {"metadata": {"hash": "fake-hash", "mode": "default-mode", "tag": "20240523"}}


@pytest.fixture(scope="session")
def dasface_face_too_small_response():
    return {
        "code": "FaceTooSmallForIAS",
        "message": "Face bounding box width is too small",
        "status": "error",
    }


@pytest.fixture(scope="session")
def dasface_form_validation_response():
    return {
        "code": "FormValidationError",
        "message": "Incorrect parameters in VerificationPhotoRequestForm.",
        "status": "error",
    }


@pytest.fixture(scope="session")
def dasface_verification_response():
    return {"confidence": 0.9876}


@pytest.fixture(scope="session")
def dasface_unknown_code_response():
    return {"code": "SomethingNobodyHasSeenYet", "message": "who knows", "status": "error"}
