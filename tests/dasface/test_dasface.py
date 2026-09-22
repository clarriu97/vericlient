import base64

import pytest
import requests_mock
from pydantic import ValidationError

from vericlient import DasfaceClient
from vericlient.dasface.exceptions import (
    DasfaceApiError,
    FaceTooSmallForIasError,
    FormValidationError,
    VideoExtractionError,
)
from vericlient.dasface.models import (
    GenerateCredentialInput,
    GenerateCredentialOutput,
    GetModelMetadataFromCredentialInput,
    ModelsOutput,
    VerifyCredentialInput,
    VerifyPhotoInput,
    VerifyVideoInput,
)
from vericlient.exceptions import InvalidCredentialError

SANDBOX_EU = "https://api-work.eu.veri-das.com/dasface/v2"


# ---------------------------------------------------------------------------
# Mocked
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_dasface_url_is_served_under_v2():
    """das-Face is the one API on /v2; das-Peak and VCSP are on /v1."""
    assert DasfaceClient(apikey="fake-apikey").url == SANDBOX_EU


@pytest.mark.dasface
def test_get_models(dasface_client, mock_server, dasface_models_response):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_get_models")

    mock_server.get(f"{SANDBOX_EU}/models", json=dasface_models_response)

    response = dasface_client.get_models()

    assert isinstance(response, ModelsOutput)
    assert [model.mode for model in response.models] == ["default-mode", "document-mode"]
    assert response.models[0].length == 128


@pytest.mark.dasface
def test_generate_credential_sends_a_base64_json_body(
    dasface_client,
    mock_server,
    dasface_credential_response,
    face_image,
):
    """das-Face takes JSON with a base64 image, not a multipart part.

    Asserted on the request body rather than only the URL: sending a multipart form here
    would still match the endpoint and still look like a pass.
    """
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_generate_credential")

    mock_server.post(
        f"{SANDBOX_EU}/models/inemex/default-mode/credential/photo",
        json=dasface_credential_response,
    )

    response = dasface_client.generate_credential(GenerateCredentialInput(image=face_image))

    assert isinstance(response, GenerateCredentialOutput)
    assert response.credential == "fake-credential"

    sent = mock_server.last_request.json()
    assert list(sent) == ["targetImage"]
    assert base64.b64decode(sent["targetImage"]) == face_image


@pytest.mark.dasface
def test_generate_credential_with_a_pinned_model(
    dasface_client,
    mock_server,
    dasface_credential_response,
    face_image,
):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_generate_credential_with_a_pinned_model")

    mock_server.post(f"{SANDBOX_EU}/models/a-hash/document-mode/credential/photo", json=dasface_credential_response)

    dasface_client.generate_credential(
        GenerateCredentialInput(image=face_image, hash="a-hash", mode="document-mode"),
    )

    assert mock_server.last_request.path.endswith("/models/a-hash/document-mode/credential/photo")


@pytest.mark.dasface
def test_a_hash_without_a_mode_is_rejected_before_any_request(face_image):
    """The model key is hash and mode together, so half of it is not enough."""
    with pytest.raises(ValueError, match="mode is required"):
        GenerateCredentialInput(image=face_image, hash="a-hash")


@pytest.mark.dasface
def test_an_image_must_be_a_path_or_bytes():
    with pytest.raises(ValidationError):
        GenerateCredentialInput(image=123)


@pytest.mark.dasface
@pytest.mark.parametrize(
    ("response_fixture", "expected"),
    [
        ("dasface_face_too_small_response", FaceTooSmallForIasError),
        ("dasface_form_validation_response", FormValidationError),
        ("dasface_unknown_code_response", DasfaceApiError),
    ],
)
def test_error_codes_become_exceptions(dasface_client, mock_server, request, response_fixture, expected, face_image):
    """Every error code maps to something meaningful, including ones not seen before.

    das-Face documents only status codes, so the set of codes is open-ended. An unrecognised
    one surfaces as DasfaceApiError carrying it, rather than disappearing into a generic
    server error.
    """
    if not mock_server:
        pytest.skip("These are mocked error bodies")

    body = request.getfixturevalue(response_fixture)
    mock_server.post(f"{SANDBOX_EU}/models/inemex/default-mode/credential/photo", json=body, status_code=400)

    with pytest.raises(expected):
        dasface_client.generate_credential(GenerateCredentialInput(image=face_image))


@pytest.mark.dasface
def test_an_unknown_code_carries_it_through(dasface_client, mock_server, dasface_unknown_code_response, face_image):
    if not mock_server:
        pytest.skip("This is a mocked error body")

    mock_server.post(
        f"{SANDBOX_EU}/models/inemex/default-mode/credential/photo",
        json=dasface_unknown_code_response,
        status_code=400,
    )

    with pytest.raises(DasfaceApiError) as raised:
        dasface_client.generate_credential(GenerateCredentialInput(image=face_image))

    assert raised.value.code == "SomethingNobodyHasSeenYet"
    assert "who knows" in str(raised.value)


@pytest.mark.dasface
def test_a_credential_the_service_cannot_read_is_reported_as_invalid(dasface_client, mock_server):
    """FormatNumberError and CorruptedSecretError both mean the same thing to a caller."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_an_unreadable_credential_is_rejected")

    for code in ("FormatNumberError", "CorruptedSecretError"):
        with requests_mock.Mocker() as mocked:
            mocked.post(
                f"{SANDBOX_EU}/models/metadata/from-credential",
                json={"code": code, "message": "", "status": "error"},
                status_code=400,
            )
            with pytest.raises(InvalidCredentialError):
                dasface_client.get_model_metadata_from_credential(
                    GetModelMetadataFromCredentialInput(credential="nope"),
                )


# ---------------------------------------------------------------------------
# Real infrastructure
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_real_alive(real_dasface):
    assert real_dasface.alive()


@pytest.mark.dasface
def test_real_get_models(real_dasface):
    """The service offers several modes, and the same hash appears once per mode."""
    models = real_dasface.get_models().models

    assert models
    assert {model.mode for model in models} >= {"default-mode", "document-mode"}
    assert all(model.hash and model.tag and model.length for model in models)


@pytest.mark.dasface
def test_real_generate_credential(real_dasface, face_image_path, face_image):
    """A credential comes back for the default model, from a path and from bytes alike."""
    from_path = real_dasface.generate_credential(GenerateCredentialInput(image=face_image_path))
    assert from_path.credential
    assert from_path.model.hash
    assert from_path.model.mode == "default-mode"

    from_bytes = real_dasface.generate_credential(GenerateCredentialInput(image=face_image))
    assert from_bytes.model.hash == from_path.model.hash


@pytest.mark.dasface
def test_real_generate_credential_with_a_pinned_model(real_dasface, face_image_path):
    """Pinning a model is honoured, and the response says which one was used."""
    model = next(m for m in real_dasface.get_models().models if m.mode == "default-mode")

    credential = real_dasface.generate_credential(
        GenerateCredentialInput(image=face_image_path, hash=model.hash, mode=model.mode),
    )

    assert credential.model.hash == model.hash
    assert credential.model.mode == model.mode


@pytest.mark.dasface
def test_real_model_metadata_points_back_at_the_generating_model(real_dasface, face_image_path):
    credential = real_dasface.generate_credential(GenerateCredentialInput(image=face_image_path))

    metadata = real_dasface.get_model_metadata_from_credential(
        GetModelMetadataFromCredentialInput(credential=credential.credential),
    ).metadata

    assert metadata.hash == credential.model.hash
    assert metadata.mode == credential.model.mode
    assert metadata.tag


@pytest.mark.dasface
def test_real_an_unreadable_credential_is_rejected(real_dasface):
    """A credential the service cannot decrypt surfaces as InvalidCredentialError.

    The value has to be valid base64 to get this far: `not-a-credential` fails earlier, on
    padding, and comes back as a FormValidationError instead. das-Face has three different
    codes for three ways of handing it a bad credential.
    """
    with pytest.raises(InvalidCredentialError):
        real_dasface.get_model_metadata_from_credential(
            GetModelMetadataFromCredentialInput(credential="AAAA"),
        )


@pytest.mark.dasface
def test_real_a_credential_that_is_not_base64_is_reported_differently(real_dasface):
    """Padding is checked before decryption, and says so."""
    with pytest.raises(FormValidationError, match="padding"):
        real_dasface.get_model_metadata_from_credential(
            GetModelMetadataFromCredentialInput(credential="not-a-credential"),
        )


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_verify_photo_sends_both_images_base64(
    dasface_client,
    mock_server,
    dasface_verification_response,
    face_image,
    other_face_image,
):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_verify_photo")

    mock_server.post(f"{SANDBOX_EU}/verification/photo", json=dasface_verification_response)

    response = dasface_client.verify_photo(
        VerifyPhotoInput(anchor_image=face_image, target_image=other_face_image),
    )

    assert response.confidence == 0.9876

    sent = mock_server.last_request.json()
    assert sorted(sent) == ["anchorImage", "targetImage"]
    assert base64.b64decode(sent["anchorImage"]) == face_image
    assert base64.b64decode(sent["targetImage"]) == other_face_image


@pytest.mark.dasface
def test_verify_photo_omits_the_mode_unless_given(
    dasface_client,
    mock_server,
    dasface_verification_response,
    face_image,
):
    """An absent optional field is left out rather than sent as null.

    das-Face rejects fields it does not recognise, so sending a key it did not ask for is not
    harmless — `rotatePhotos` is documented in v3.26 and refused by the service.
    """
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_verify_photo_with_a_mode")

    mock_server.post(f"{SANDBOX_EU}/verification/photo", json=dasface_verification_response)

    dasface_client.verify_photo(VerifyPhotoInput(anchor_image=face_image, target_image=face_image))
    assert "mode" not in mock_server.last_request.json()

    dasface_client.verify_photo(
        VerifyPhotoInput(anchor_image=face_image, target_image=face_image, mode="document-mode"),
    )
    assert mock_server.last_request.json()["mode"] == "document-mode"


@pytest.mark.dasface
def test_verify_credential_sends_the_credential_verbatim(
    dasface_client,
    mock_server,
    dasface_verification_response,
    face_image,
):
    """The credential is already text, so it goes as-is rather than being encoded again."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_verify_credential")

    mock_server.post(f"{SANDBOX_EU}/verification/credential", json=dasface_verification_response)

    dasface_client.verify_credential(
        VerifyCredentialInput(anchor_image=face_image, target_credential="a-credential"),
    )

    sent = mock_server.last_request.json()
    assert sent["targetCredential"] == "a-credential"
    assert base64.b64decode(sent["anchorImage"]) == face_image


@pytest.mark.dasface
def test_verify_video_sends_the_video_base64(
    dasface_client,
    mock_server,
    dasface_verification_response,
    face_image,
    face_video,
):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_verify_video")

    mock_server.post(f"{SANDBOX_EU}/verification/video", json=dasface_verification_response)

    dasface_client.verify_video(VerifyVideoInput(anchor_image=face_image, target_video=face_video))

    sent = mock_server.last_request.json()
    assert sorted(sent) == ["anchorImage", "targetVideo"]
    assert base64.b64decode(sent["targetVideo"]) == face_video


@pytest.mark.dasface
def test_real_verify_photo(real_dasface, face_image_path, other_face_image_path):
    """The same face matches itself, a different face does not, by a wide margin."""
    same = real_dasface.verify_photo(
        VerifyPhotoInput(anchor_image=face_image_path, target_image=face_image_path),
    )
    different = real_dasface.verify_photo(
        VerifyPhotoInput(anchor_image=face_image_path, target_image=other_face_image_path),
    )

    assert same.confidence > 0.9
    assert different.confidence < 0.1
    assert same.confidence > different.confidence


@pytest.mark.dasface
def test_real_verify_photo_with_a_mode(real_dasface, face_image_path):
    """A mode is accepted. `rotatePhotos`, which v3.26 documents, is not — see #30."""
    response = real_dasface.verify_photo(
        VerifyPhotoInput(anchor_image=face_image_path, target_image=face_image_path, mode="default-mode"),
    )
    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_verify_credential(real_dasface, face_image_path):
    """The everyday flow: enrol once into a credential, then verify fresh photos against it."""
    credential = real_dasface.generate_credential(
        GenerateCredentialInput(image=face_image_path),
    ).credential

    response = real_dasface.verify_credential(
        VerifyCredentialInput(anchor_image=face_image_path, target_credential=credential),
    )

    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_verify_video(real_dasface, face_image_path, face_video_path):
    response = real_dasface.verify_video(
        VerifyVideoInput(anchor_image=face_image_path, target_video=face_video_path),
    )
    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_a_video_that_is_not_a_video_is_reported(real_dasface, face_image_path):
    """Undecodable video is its own failure, not a generic bad request."""
    with pytest.raises(VideoExtractionError):
        real_dasface.verify_video(
            VerifyVideoInput(anchor_image=face_image_path, target_video=b"x" * 5000),
        )
