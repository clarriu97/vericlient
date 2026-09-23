import base64
import json

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


@pytest.fixture
def real_model(real_dasface):
    """Return the model the real tests generate credentials with.

    There is no endpoint that lets the service pick one, so every credential test has to
    name a model; the newest `default-mode` one is the sensible choice.
    """
    models = [model for model in real_dasface.get_models().models if model.mode == "default-mode"]
    return max(models, key=lambda model: model.tag)


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
def dasface_field_validation_response():
    """Return the useful half of a validation failure: which field, and what is wrong with it."""
    return {
        "code": "FormValidationError",
        "errors": [["length", "Number must be between 1 and 6."]],
        "message": "Incorrect parameters in GenerateSequentialChallengeForm",
        "status": "error",
    }


@pytest.fixture(scope="session")
def dasface_verification_response():
    return {"confidence": 0.9876}


@pytest.fixture(scope="session")
def dasface_photo_authenticity_response():
    return {"confidence": 0.8765}


@pytest.fixture(scope="session")
def dasface_video_authenticity_response():
    return {"authenticity": 0.86, "similarity": 0.99}


@pytest.fixture(scope="session")
def dasface_challenge_payload():
    """Return the challenge as it is found inside the token, shaped as the service sends it."""
    return {
        "schema": "https://veridas.com/dasface/schemas/chief-v0.0.0.json",
        "id": "f6ba1c2d3e4f5061728394a5b6c7d8e9",
        "timestamp": "2026-09-23T04:17:54.505635+00:00",
        "expires": "2026-09-23T04:47:54.505635+00:00",
        "challenge": {
            "class": "sequential",
            "actions": [
                {"class": "move-head-and-back", "name": "action-0", "parameters": {"direction": "right"}},
                {"class": "move-head-and-back", "name": "action-1", "parameters": {"direction": "top"}},
            ],
        },
    }


@pytest.fixture(scope="session")
def dasface_challenge_token(dasface_challenge_payload):
    """Return a token shaped like the real one: three base64url segments, unpadded.

    Only the payload has to be real, since the client reads that and never checks the
    signature.
    """

    def segment(content: bytes) -> str:
        return base64.urlsafe_b64encode(content).decode().rstrip("=")

    return ".".join(
        [
            segment(json.dumps({"typ": "JWT", "alg": "ES512"}).encode()),
            segment(json.dumps(dasface_challenge_payload).encode()),
            segment(b"a signature this client never checks"),
        ],
    )


@pytest.fixture(scope="session")
def dasface_challenge_analysis_response():
    return {"confidence": 0.9556, "errors": []}


@pytest.fixture(scope="session")
def dasface_challenge_failed_analysis_response():
    """Return the shape this endpoint reports a failure with: a 200, no confidence, errors."""
    return {
        "confidence": None,
        "errors": [["FaceTooSmallForIAS", "Face bounding box width is too small"]],
    }


@pytest.fixture(scope="session")
def dasface_expired_challenge_response():
    return {
        "code": "ExpiredOrInvalidChallengeError",
        "message": "Given challenge is expired or invalid",
        "status": "error",
    }


@pytest.fixture(scope="session")
def annotations_path() -> str:
    """Return WebVTT annotations of a challenge recording, as the capture SDK produces them."""
    return "tests/dasface/resources/annotations.vtt"


@pytest.fixture(scope="session")
def annotations(annotations_path) -> bytes:
    with open(annotations_path, "rb") as f:
        return f.read()


@pytest.fixture(scope="session")
def dasface_unknown_code_response():
    return {"code": "SomethingNobodyHasSeenYet", "message": "who knows", "status": "error"}
