import base64
import inspect
import warnings
from datetime import UTC, datetime

import pytest
import requests_mock
from pydantic import ValidationError

from vericlient import DasfaceClient
from vericlient.dasface.exceptions import (
    DasfaceApiError,
    ExpiredOrInvalidChallengeError,
    FaceNotFoundError,
    FaceTooSmallForIasError,
    FormValidationError,
    InvalidVideoMetadataError,
    UnknownHashAndModeError,
    VideoExtractionError,
)
from vericlient.dasface.models import (
    GenerateCredentialInput,
    GenerateCredentialOutput,
    ModelsOutput,
    VerifyPhotoInput,
)
from vericlient.exceptions import InvalidCredentialError, ServerError

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
        f"{SANDBOX_EU}/models/a-hash/default-mode/credential/photo",
        json=dasface_credential_response,
    )

    response = dasface_client.generate_credential(
        image=face_image,
        hash="a-hash",
        mode="default-mode",
    )

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
        image=face_image,
        hash="a-hash",
        mode="document-mode",
    )

    assert mock_server.last_request.path.endswith("/models/a-hash/document-mode/credential/photo")


@pytest.mark.dasface
@pytest.mark.parametrize("model", [{"hash": "a-hash"}, {"mode": "default-mode"}])
def test_half_a_model_key_is_rejected_before_any_request(face_image, model):
    """The model key is hash and mode together, so half of it is not enough."""
    with pytest.raises(ValueError, match="go together"):
        GenerateCredentialInput(image=face_image, **model)


@pytest.mark.dasface
def test_a_credential_cannot_be_generated_without_naming_a_model(face_image):
    """There is no endpoint that lets the service choose the model.

    `POST /v2/credential/photo` did that, and the specification deprecated it in v3.26 and
    dropped it in v3.35; `work`/`eu` does not route it. The only model-less form left is the
    INE Mexico one, so asking for a credential without a model has to fail here rather than
    silently generate one against whichever model an arbitrary endpoint happens to resolve to.
    """
    with pytest.raises(ValueError, match="required"):
        GenerateCredentialInput(image=face_image)


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
    mock_server.post(f"{SANDBOX_EU}/models/a-hash/default-mode/credential/photo", json=body, status_code=400)

    with pytest.raises(expected):
        dasface_client.generate_credential(
            image=face_image,
            hash="a-hash",
            mode="default-mode",
        )


@pytest.mark.dasface
def test_an_unknown_code_carries_it_through(dasface_client, mock_server, dasface_unknown_code_response, face_image):
    if not mock_server:
        pytest.skip("This is a mocked error body")

    mock_server.post(
        f"{SANDBOX_EU}/models/a-hash/default-mode/credential/photo",
        json=dasface_unknown_code_response,
        status_code=400,
    )

    with pytest.raises(DasfaceApiError) as raised:
        dasface_client.generate_credential(
            image=face_image,
            hash="a-hash",
            mode="default-mode",
        )

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
                    credential="nope",
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
def test_real_generate_credential(real_dasface, real_model, face_image_path, face_image):
    """A credential comes back from a path and from bytes alike, for the model asked for."""
    from_path = real_dasface.generate_credential(
        image=face_image_path,
        hash=real_model.hash,
        mode=real_model.mode,
    )
    assert from_path.credential
    assert from_path.model.hash == real_model.hash
    assert from_path.model.mode == real_model.mode

    from_bytes = real_dasface.generate_credential(
        image=face_image,
        hash=real_model.hash,
        mode=real_model.mode,
    )
    assert from_bytes.model.hash == from_path.model.hash


@pytest.mark.dasface
def test_real_model_metadata_points_back_at_the_generating_model(real_dasface, real_model, face_image_path):
    credential = real_dasface.generate_credential(
        image=face_image_path,
        hash=real_model.hash,
        mode=real_model.mode,
    )

    metadata = real_dasface.get_model_metadata_from_credential(
        credential=credential.credential,
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
            credential="AAAA",
        )


@pytest.mark.dasface
def test_real_a_credential_that_is_not_base64_is_reported_differently(real_dasface):
    """Padding is checked before decryption, and says so."""
    with pytest.raises(FormValidationError, match="padding"):
        real_dasface.get_model_metadata_from_credential(
            credential="not-a-credential",
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
        anchor_image=face_image,
        target_image=other_face_image,
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

    dasface_client.verify_photo(anchor_image=face_image, target_image=face_image)
    assert "mode" not in mock_server.last_request.json()

    dasface_client.verify_photo(
        anchor_image=face_image,
        target_image=face_image,
        mode="document-mode",
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
        anchor_image=face_image,
        target_credential="a-credential",
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

    dasface_client.verify_video(anchor_image=face_image, target_video=face_video)

    sent = mock_server.last_request.json()
    assert sorted(sent) == ["anchorImage", "targetVideo"]
    assert base64.b64decode(sent["targetVideo"]) == face_video


@pytest.mark.dasface
def test_real_verify_photo(real_dasface, face_image_path, other_face_image_path):
    """The same face matches itself, a different face does not, by a wide margin."""
    same = real_dasface.verify_photo(
        anchor_image=face_image_path,
        target_image=face_image_path,
    )
    different = real_dasface.verify_photo(
        anchor_image=face_image_path,
        target_image=other_face_image_path,
    )

    assert same.confidence > 0.9
    assert different.confidence < 0.1
    assert same.confidence > different.confidence


@pytest.mark.dasface
def test_real_verify_photo_with_a_mode(real_dasface, face_image_path):
    """A mode is accepted. `rotatePhotos`, which v3.26 documents, is not — see #30."""
    response = real_dasface.verify_photo(
        anchor_image=face_image_path,
        target_image=face_image_path,
        mode="default-mode",
    )
    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_verify_credential(real_dasface, real_model, face_image_path):
    """The everyday flow: enrol once into a credential, then verify fresh photos against it."""
    credential = real_dasface.generate_credential(
        image=face_image_path,
        hash=real_model.hash,
        mode=real_model.mode,
    ).credential

    response = real_dasface.verify_credential(
        anchor_image=face_image_path,
        target_credential=credential,
    )

    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_verify_video(real_dasface, face_image_path, face_video_path):
    response = real_dasface.verify_video(
        anchor_image=face_image_path,
        target_video=face_video_path,
    )
    assert response.confidence > 0.9


@pytest.mark.dasface
def test_real_a_video_that_is_not_a_video_is_reported(real_dasface, face_image_path):
    """Undecodable video is its own failure, not a generic bad request."""
    with pytest.raises(VideoExtractionError):
        real_dasface.verify_video(
            anchor_image=face_image_path,
            target_video=b"x" * 5000,
        )


# ---------------------------------------------------------------------------
# Authenticity
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_check_photo_authenticity_sends_the_image_as_target(
    dasface_client,
    mock_server,
    dasface_photo_authenticity_response,
    face_image,
):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_check_photo_authenticity")

    mock_server.post(f"{SANDBOX_EU}/authenticity/photo", json=dasface_photo_authenticity_response)

    response = dasface_client.check_photo_authenticity(image=face_image)

    assert response.confidence == 0.8765
    sent = mock_server.last_request.json()
    assert list(sent) == ["targetImage"]
    assert base64.b64decode(sent["targetImage"]) == face_image


@pytest.mark.dasface
def test_check_video_authenticity_returns_both_figures(
    dasface_client,
    mock_server,
    dasface_video_authenticity_response,
    face_image,
    face_video,
):
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_check_video_authenticity")

    mock_server.post(f"{SANDBOX_EU}/authenticity/video/photo", json=dasface_video_authenticity_response)

    response = dasface_client.check_video_authenticity(
        anchor_image=face_image,
        target_video=face_video,
    )

    assert response.authenticity == 0.86
    assert response.similarity == 0.99


@pytest.mark.dasface
def test_real_check_photo_authenticity(real_dasface, face_image_path):
    """A genuine photo of a face scores high."""
    response = real_dasface.check_photo_authenticity(image=face_image_path)
    assert response.confidence > 0.5


@pytest.mark.dasface
def test_real_authenticity_rejects_a_face_that_is_too_small(real_dasface, other_face_image_path):
    """Too small a face is refused outright rather than scored low.

    Worth pinning: a low score and a refusal mean different things to a caller, and this is
    the one place in das-Face where image size alone decides.
    """
    with pytest.raises(FaceTooSmallForIasError):
        real_dasface.check_photo_authenticity(image=other_face_image_path)


@pytest.mark.dasface
def test_real_check_video_authenticity(real_dasface, face_image_path, face_video_path):
    """Authenticity and similarity are independent, and both come back."""
    response = real_dasface.check_video_authenticity(
        anchor_image=face_image_path,
        target_video=face_video_path,
    )

    assert response.authenticity > 0.5
    assert response.similarity > 0.9


@pytest.mark.dasface
def test_inemex_uses_its_own_path(dasface_client, mock_server, dasface_credential_response, face_image):
    """The INE Mexico variant lives under a different prefix, not a different body."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_generate_credential_with_inemex")

    mock_server.post(f"{SANDBOX_EU}/inemex/models/a-hash/default-mode/credential/photo", json=dasface_credential_response)

    dasface_client.generate_credential(
        image=face_image,
        hash="a-hash",
        mode="default-mode",
        inemex=True,
    )

    assert mock_server.last_request.path.endswith("/inemex/models/a-hash/default-mode/credential/photo")


@pytest.mark.dasface
def test_inemex_without_a_model_uses_its_default_model_path(
    dasface_client,
    mock_server,
    dasface_credential_response,
    face_image,
):
    """The INE Mexico endpoint is the only one with a default-model form."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_generate_credential_with_inemex_default_model")

    mock_server.post(f"{SANDBOX_EU}/models/inemex/default-mode/credential/photo", json=dasface_credential_response)

    dasface_client.generate_credential(image=face_image, inemex=True)

    assert mock_server.last_request.path.endswith("/models/inemex/default-mode/credential/photo")


@pytest.mark.dasface
def test_real_generate_credential_with_inemex_default_model(real_dasface, real_model, face_image_path):
    """Its default model is a specific one, and not the newest the service offers.

    Worth asserting: the endpoint reads as a generic default, and it is not. It resolves to
    an older model than `get_models()` leads with, so a credential made here does not compare
    against one made with the current model.
    """
    credential = real_dasface.generate_credential(image=face_image_path, inemex=True)

    assert credential.credential
    assert credential.model.mode == "default-mode"
    assert credential.model.hash != real_model.hash


@pytest.mark.dasface
def test_real_generate_credential_with_inemex(real_dasface, real_model, face_image_path):
    """The INE Mexico variant answers with a credential from the model that was asked for.

    It needs a specific agreement with Veridas, so it may not be enabled everywhere; it is on
    the subscription this runs against.
    """
    credential = real_dasface.generate_credential(
        image=face_image_path,
        hash=real_model.hash,
        mode=real_model.mode,
        inemex=True,
    )

    assert credential.credential
    assert credential.model.hash == real_model.hash


@pytest.mark.dasface
def test_generate_sequential_challenge_reads_the_actions_out_of_the_token(
    dasface_client,
    mock_server,
    dasface_challenge_token,
):
    """The service answers with a signed token, not JSON, and the actions live inside it."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_generate_sequential_challenge")

    mock_server.post(
        f"{SANDBOX_EU}/challenges/generation/sequential",
        text=dasface_challenge_token,
        headers={"Content-Type": "application/jose"},
    )

    challenge = dasface_client.generate_sequential_challenge(length=2)

    assert challenge.token == dasface_challenge_token
    assert challenge.id == "f6ba1c2d3e4f5061728394a5b6c7d8e9"
    assert [action.name for action in challenge.actions] == ["action-0", "action-1"]
    assert [action.action_class for action in challenge.actions] == ["move-head-and-back"] * 2
    assert [action.parameters["direction"] for action in challenge.actions] == ["right", "top"]
    assert mock_server.last_request.json() == {"length": 2}


@pytest.mark.dasface
def test_generate_sequential_challenge_sends_nothing_it_was_not_given(
    dasface_client,
    mock_server,
    dasface_challenge_token,
):
    """The service has its own defaults, so an empty request has to stay empty."""
    if not mock_server:
        pytest.skip("Asserted on the request body")

    mock_server.post(f"{SANDBOX_EU}/challenges/generation/sequential", text=dasface_challenge_token)

    dasface_client.generate_sequential_challenge()

    assert mock_server.last_request.json() == {}


@pytest.mark.dasface
def test_a_token_that_cannot_be_read_is_a_server_error(dasface_client, mock_server):
    """A 200 whose token is not a token is the service breaking its own contract."""
    if not mock_server:
        pytest.skip("This is a mocked response body")

    mock_server.post(f"{SANDBOX_EU}/challenges/generation/sequential", text="not a token")

    with pytest.raises(ServerError):
        dasface_client.generate_sequential_challenge()


@pytest.mark.dasface
def test_analyse_challenge_response_sends_the_token_verbatim(
    dasface_client,
    mock_server,
    dasface_challenge_token,
    dasface_challenge_analysis_response,
    face_image,
    face_video,
    annotations,
):
    """Everything is base64 except the token, which has to arrive exactly as it was issued."""
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_analyse_challenge_response")

    mock_server.post(
        f"{SANDBOX_EU}/challenges/analysis/video-photo",
        json=dasface_challenge_analysis_response,
    )

    response = dasface_client.analyse_challenge_response(
        token=dasface_challenge_token,
        annotations=annotations,
        anchor_image=face_image,
        target_video=face_video,
    )

    assert response.confidence == dasface_challenge_analysis_response["confidence"]
    assert response.errors == []

    sent = mock_server.last_request.json()
    assert sent["token"] == dasface_challenge_token
    assert base64.b64decode(sent["annotations"]) == annotations
    assert base64.b64decode(sent["anchorImage"]) == face_image
    assert base64.b64decode(sent["targetVideo"]) == face_video


@pytest.mark.dasface
def test_a_failed_analysis_comes_back_as_a_result_rather_than_an_exception(
    dasface_client,
    mock_server,
    dasface_challenge_token,
    dasface_challenge_failed_analysis_response,
    face_image,
    face_video,
    annotations,
):
    """Failures come back in a 200 here, which no other das-Face endpoint does.

    A face too small to analyse raises everywhere else. Here it arrives as a null confidence
    with the reason beside it, so the client hands both back instead of inventing an
    exception the service did not raise.
    """
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_analysis_reports_a_face_that_is_too_small")

    mock_server.post(
        f"{SANDBOX_EU}/challenges/analysis/video-photo",
        json=dasface_challenge_failed_analysis_response,
    )

    response = dasface_client.analyse_challenge_response(
        token=dasface_challenge_token,
        annotations=annotations,
        anchor_image=face_image,
        target_video=face_video,
    )

    assert response.confidence is None
    assert [(error.code, error.message) for error in response.errors] == [
        ("FaceTooSmallForIAS", "Face bounding box width is too small"),
    ]


@pytest.mark.dasface
def test_an_expired_challenge_is_reported_as_such(
    dasface_client,
    mock_server,
    dasface_challenge_token,
    dasface_expired_challenge_response,
    face_image,
    face_video,
    annotations,
):
    if not mock_server:
        pytest.skip("Reaching this for real means waiting out a challenge, five minutes at least")

    mock_server.post(
        f"{SANDBOX_EU}/challenges/analysis/video-photo",
        json=dasface_expired_challenge_response,
        status_code=400,
    )

    with pytest.raises(ExpiredOrInvalidChallengeError):
        dasface_client.analyse_challenge_response(
            token=dasface_challenge_token,
            annotations=annotations,
            anchor_image=face_image,
            target_video=face_video,
        )


@pytest.mark.dasface
def test_real_generate_sequential_challenge(real_dasface):
    """The challenge names the actions to prompt for, and says when it stops being valid."""
    challenge = real_dasface.generate_sequential_challenge(length=3, expiration=300)

    assert challenge.token.count(".") == 2
    assert len(challenge.actions) == 3
    assert [action.name for action in challenge.actions] == ["action-0", "action-1", "action-2"]
    assert all(action.action_class for action in challenge.actions)
    assert challenge.expires > challenge.timestamp
    assert challenge.expires > datetime.now(tz=UTC)


@pytest.mark.dasface
def test_real_a_challenge_length_out_of_range_is_refused(real_dasface):
    """1 to 6, and the service says which field and which range."""
    with pytest.raises(FormValidationError, match="between 1 and 6"):
        real_dasface.generate_sequential_challenge(length=9)


@pytest.mark.dasface
def test_real_analyse_challenge_response(real_dasface, face_image_path, face_video_path, annotations_path):
    """A recording is analysed against the challenge it was issued for.

    The confidence itself is not asserted: this video was not recorded performing these
    actions, and the actions are random, so the score is whatever the analysis makes of it.
    What matters here is that the round trip works and the service reports no errors.
    """
    challenge = real_dasface.generate_sequential_challenge()

    response = real_dasface.analyse_challenge_response(
        token=challenge.token,
        annotations=annotations_path,
        anchor_image=face_image_path,
        target_video=face_video_path,
    )

    assert response.errors == []
    assert 0 <= response.confidence <= 1


@pytest.mark.dasface
def test_real_analysis_reports_a_face_that_is_too_small(
    real_dasface,
    other_face_image_path,
    face_video_path,
    annotations_path,
):
    """The same condition that raises elsewhere arrives here as a null confidence."""
    challenge = real_dasface.generate_sequential_challenge()

    response = real_dasface.analyse_challenge_response(
        token=challenge.token,
        annotations=annotations_path,
        anchor_image=other_face_image_path,
        target_video=face_video_path,
    )

    assert response.confidence is None
    assert [error.code for error in response.errors] == ["FaceTooSmallForIAS"]


@pytest.mark.dasface
def test_real_a_tampered_token_is_refused(real_dasface, face_image_path, face_video_path, annotations_path):
    """The signature is the point of the token, and the service checks it."""
    challenge = real_dasface.generate_sequential_challenge()
    header, payload, signature = challenge.token.split(".")
    tampered = f"{header}.{payload[:-4]}AAAA.{signature}"

    with pytest.raises(FormValidationError, match=r"signature|Token"):
        real_dasface.analyse_challenge_response(
            token=tampered,
            annotations=annotations_path,
            anchor_image=face_image_path,
            target_video=face_video_path,
        )


@pytest.mark.dasface
def test_a_validation_failure_names_the_field(dasface_client, mock_server, dasface_field_validation_response):
    """The service's `message` names the form; only its `errors` say what is wrong.

    `Incorrect parameters in GenerateSequentialChallengeForm` on its own tells a caller
    nothing actionable, so the field errors are carried through rather than dropped.
    """
    if not mock_server:
        pytest.skip("Covered against the real service by test_real_a_challenge_length_out_of_range_is_refused")

    mock_server.post(
        f"{SANDBOX_EU}/challenges/generation/sequential",
        json=dasface_field_validation_response,
        status_code=400,
    )

    with pytest.raises(FormValidationError) as raised:
        dasface_client.generate_sequential_challenge(length=9)

    assert raised.value.errors == [("length", "Number must be between 1 and 6.")]
    assert "length: Number must be between 1 and 6." in str(raised.value)


# ---------------------------------------------------------------------------
# Error paths, provoked against the real service rather than mocked.
#
# A mocked error body only proves the client maps a code it was handed. These send input the
# service genuinely rejects, which is what catches a mapping built on a wrong assumption.
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_real_an_image_with_no_face_is_refused_everywhere(real_dasface, real_model, no_face_image_path):
    """The same input fails the same way on all three endpoints that read a face."""
    with pytest.raises(FaceNotFoundError):
        real_dasface.generate_credential(
            image=no_face_image_path,
            hash=real_model.hash,
            mode=real_model.mode,
        )

    with pytest.raises(FaceNotFoundError):
        real_dasface.verify_photo(anchor_image=no_face_image_path, target_image=no_face_image_path)

    with pytest.raises(FaceNotFoundError):
        real_dasface.check_photo_authenticity(image=no_face_image_path)


@pytest.mark.dasface
def test_real_an_unknown_mode_is_refused(real_dasface, real_model, face_image_path):
    """A real model with a mode it does not run in.

    The hash has to be real: the gateway only routes model paths it knows, so a made-up hash
    never reaches the service to be judged.
    """
    with pytest.raises(UnknownHashAndModeError):
        real_dasface.generate_credential(
            image=face_image_path,
            hash=real_model.hash,
            mode="no-such-mode",
        )


@pytest.mark.dasface
def test_real_a_video_with_nobody_in_it_is_refused(real_dasface, face_image_path, no_face_video_path):
    """A video the service cannot use, reported under a name that does not fit.

    The video is one second of flat grey at 25 frames per second, so its frame count and
    frame rate are both fine and only the missing face is not. The service answers
    `InvalidNumFramesVideoError` with a null message. Asserted as it behaves, not as it
    reads; reported in #30.
    """
    with pytest.raises(InvalidVideoMetadataError):
        real_dasface.verify_video(anchor_image=face_image_path, target_video=no_face_video_path)


@pytest.mark.dasface
def test_real_an_empty_video_is_refused(real_dasface, face_image_path, empty_file_path):
    with pytest.raises(FormValidationError):
        real_dasface.verify_video(anchor_image=face_image_path, target_video=empty_file_path)


@pytest.mark.dasface
def test_real_two_faces_in_one_photo_are_not_refused(real_dasface, real_model, two_people_image_path, face_image_path):
    """das-Face does not raise `MoreThanOneFaceError`; it picks a face and says nothing.

    This pins down behaviour rather than endorsing it. The specification documents the error
    for exactly this input, the service does not raise it, and the face it settles on is the
    one on the right — not the first, and not the caller's choice. A credential comes back
    for a person the caller never selected.

    Reported as #30. If Veridas changes it, this test fails and we find out from the suite
    rather than from a user.
    """
    credential = real_dasface.generate_credential(
        image=two_people_image_path,
        hash=real_model.hash,
        mode=real_model.mode,
    )
    assert credential.credential

    against_the_left = real_dasface.verify_photo(
        anchor_image=two_people_image_path,
        target_image=face_image_path,
    )
    assert against_the_left.confidence < 0.1, "the left-hand face is the one it ignored"


# ---------------------------------------------------------------------------
# The call style these methods used to require, kept working for one version.
# ---------------------------------------------------------------------------


@pytest.mark.dasface
def test_the_old_call_style_still_works_and_warns(dasface_client, mock_server, dasface_verification_response, face_image):
    """Passing the input model is deprecated, not broken.

    Upgrading should not be a rewrite, so the model is expanded into the arguments the method
    now takes. Validation is unchanged, because the method builds the same model either way.
    """
    if not mock_server:
        pytest.skip("Asserted on the request the client builds")

    mock_server.post(f"{SANDBOX_EU}/verification/photo", json=dasface_verification_response)

    with pytest.warns(DeprecationWarning, match="VerifyPhotoInput"):
        response = dasface_client.verify_photo(VerifyPhotoInput(anchor_image=face_image, target_image=face_image))

    assert response.confidence == dasface_verification_response["confidence"]
    assert set(mock_server.last_request.json()) == {"anchorImage", "targetImage"}


@pytest.mark.dasface
def test_the_old_call_style_works_by_keyword_too(dasface_client, mock_server, dasface_verification_response, face_image):
    """Some clients spelled it `data_model=`, so that spelling has to keep working as well."""
    if not mock_server:
        pytest.skip("Asserted on the request the client builds")

    mock_server.post(f"{SANDBOX_EU}/verification/photo", json=dasface_verification_response)

    with pytest.warns(DeprecationWarning, match="VerifyPhotoInput"):
        dasface_client.verify_photo(data_model=VerifyPhotoInput(anchor_image=face_image, target_image=face_image))

    assert set(mock_server.last_request.json()) == {"anchorImage", "targetImage"}


@pytest.mark.dasface
def test_the_new_call_style_does_not_warn(dasface_client, mock_server, dasface_verification_response, face_image):
    if not mock_server:
        pytest.skip("Asserted on the request the client builds")

    mock_server.post(f"{SANDBOX_EU}/verification/photo", json=dasface_verification_response)

    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        dasface_client.verify_photo(anchor_image=face_image, target_image=face_image)


@pytest.mark.dasface
def test_validation_is_the_same_whichever_way_it_is_called(face_image):
    """The method builds the same model, so a bad call fails identically either way."""
    with pytest.raises(ValidationError, match="required"):
        GenerateCredentialInput(image=face_image)

    client = DasfaceClient(apikey="fake-apikey")
    with pytest.raises(ValidationError, match="required"):
        client.generate_credential(image=face_image)


@pytest.mark.dasface
def test_the_methods_advertise_their_arguments():
    """What the change is for: the parameters are visible without importing anything.

    Tooling reads the signature through `functools.wraps`, so the deprecation shim has to
    keep it intact rather than replacing it with `*args, **kwargs`.
    """
    signature = inspect.signature(DasfaceClient.verify_photo)

    assert list(signature.parameters) == ["self", "anchor_image", "target_image", "mode"]
    assert signature.parameters["mode"].default is None
