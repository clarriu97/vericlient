"""Implementation of the client for the das-Face service."""

import base64
import binascii
import json

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.dasface.endpoints import DasfaceEndpoints
from vericlient.dasface.exceptions import (
    DasfaceApiError,
    ExpiredOrInvalidChallengeError,
    FaceAlignmentError,
    FaceNotFoundError,
    FaceTooSmallForIasError,
    FormValidationError,
    IncompatibleCredentialsError,
    InvalidVideoMetadataError,
    MoreThanOneFaceError,
    NotEnoughVideoDataError,
    ObsoleteCredentialModelError,
    PathNotFoundError,
    UnknownHashAndModeError,
    VideoExtractionError,
    ZeroLengthVideoError,
)
from vericlient.dasface.models import (
    ChallengeAction,
    ChallengeAnalysisInput,
    ChallengeAnalysisOutput,
    ChallengeError,
    GenerateCredentialInput,
    GenerateCredentialOutput,
    GetModelMetadataFromCredentialInput,
    GetModelMetadataFromCredentialOutput,
    ModelsOutput,
    PhotoAuthenticityInput,
    PhotoAuthenticityOutput,
    SequentialChallengeInput,
    SequentialChallengeOutput,
    VerificationOutput,
    VerifyCredentialInput,
    VerifyPhotoInput,
    VerifyVideoInput,
    VideoAuthenticityInput,
    VideoAuthenticityOutput,
)
from vericlient.deprecation import legacy_model_argument
from vericlient.exceptions import InvalidCredentialError, UnsupportedMediaTypeError
from vericlient.utils import encode_base64


class DasfaceClient(Client):
    """Class to interact with the das-Face API.

    das-Face differs from the other two clients in how it is spoken to: requests carry JSON
    with base64 encoded images rather than multipart file parts, its fields are camelCase,
    and it is served under `/v2`. None of that reaches the caller — images go in as a path or
    as bytes, and attributes keep their Python names.
    """

    def __init__(
        self,
        apikey: str | None = None,
        timeout: int | None = None,
        environment: str | None = None,
        location: str | None = None,
        url: str | None = None,
        headers: dict | None = None,
    ) -> None:
        """Create the DasfaceClient class.

        Args:
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        super().__init__(
            api=APIs.DASFACE,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        # From the v3.35 specification, which enumerates these codes; v3.26 did not.
        # UnknownHashAndModeError and PathNotFoundError are not in it and were found against
        # work/eu. FormatNumberError, CorruptedSecretError and MetadataValidationError all
        # mean the credential cannot be used, which is what the caller needs to know, so they
        # share the library's own exception rather than leaking three service-internal names.
        self._exceptions = {
            "FaceNotFoundError": FaceNotFoundError,
            "MoreThanOneFaceError": MoreThanOneFaceError,
            "FaceAlignmentError": FaceAlignmentError,
            "FaceTooSmallForIAS": FaceTooSmallForIasError,
            "ObsoleteCredentialModelError": ObsoleteCredentialModelError,
            "MetadataEqError": IncompatibleCredentialsError,
            "UnknownHashAndModeError": UnknownHashAndModeError,
            "PathNotFoundError": PathNotFoundError,
            "ExpiredOrInvalidChallengeError": ExpiredOrInvalidChallengeError,
            "UnsupportedMediaTypeError": UnsupportedMediaTypeError,
            "FormatNumberError": InvalidCredentialError,
            "CorruptedSecretError": InvalidCredentialError,
            "MetadataValidationError": InvalidCredentialError,
            "ZeroLengthVideoError": ZeroLengthVideoError,
            "NotEnoughVideoDataError": NotEnoughVideoDataError,
            "VideoExtractionError": VideoExtractionError,
            "InvalidFPSVideoError": InvalidVideoMetadataError,
            "InvalidNumFramesVideoError": InvalidVideoMetadataError,
        }

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=DasfaceEndpoints.ALIVE.value)
        accepted_status_code = 204
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API.

        das-Face reports its failures as `{code, message, status}`.
        """
        payload = self._error_payload(response)
        code = payload.get("code")

        handler = self._exceptions.get(code)
        if handler:
            raise handler

        # One code covers every malformed input, and what it was is split between the message
        # and the per-field errors, so both are passed through rather than swallowed.
        if code == "FormValidationError":
            errors = [(field, reason) for field, reason in payload.get("errors") or []]
            raise FormValidationError(payload.get("message"), errors)

        # An unrecognised code still says more than a generic server error would.
        if code:
            raise DasfaceApiError(code, payload.get("message"))

        self._raise_server_error(response)

    def get_models(self) -> ModelsOutput:
        """Get the biometrics models available in the service.

        One entry per hash and mode, so the same hash appears several times.

        Returns:
            ModelsOutput: The available models

        """
        response = self._get(endpoint=DasfaceEndpoints.MODELS.value)
        return ModelsOutput(models=response.json())

    @legacy_model_argument(GenerateCredentialInput)
    def generate_credential(
        self,
        image: str | bytes,
        hash: str | None = None,  # noqa: A002
        mode: str | None = None,
        inemex: bool = False,  # noqa: FBT001, FBT002
    ) -> GenerateCredentialOutput:
        """Generate a credential from a photo.

        A credential is the biometric representation of a face, and what gets stored and
        compared later. The model is part of it, so `hash` and `mode` are required: take
        them from `get_models()`. The service has no endpoint that picks a model for you.

        Setting `inemex` uses the INE Mexico variant of the endpoint, which needs a specific
        agreement with Veridas. That one does have a default-model form, so with `inemex`
        set the model may be left out.

        Args:
            image: The photo, as a path or as bytes
            hash: The hash of the model to use, from `get_models()`
            mode: The mode to use, from `get_models()`
            inemex: Use the INE Mexico variant of the endpoint

        Returns:
            GenerateCredentialOutput: The credential and the model behind it

        Raises:
            FaceTooSmallForIasError: If the face is too small to analyse
            UnknownHashAndModeError: If no model matches that hash and mode
            FormValidationError: If the photo cannot be read

        """
        data_model = GenerateCredentialInput(image=image, hash=hash, mode=mode, inemex=inemex)
        if not data_model.inemex:
            endpoint = DasfaceEndpoints.MODEL_CREDENTIAL_PHOTO.value
        elif data_model.hash:
            endpoint = DasfaceEndpoints.INEMEX_MODEL_CREDENTIAL_PHOTO.value
        else:
            endpoint = DasfaceEndpoints.INEMEX_DEFAULT_CREDENTIAL_PHOTO.value
        if data_model.hash:
            endpoint = endpoint.replace("<hash>", data_model.hash).replace("<mode>", data_model.mode)

        response = self._post(
            endpoint=endpoint,
            json_={"targetImage": encode_base64(data_model.image)},
        )
        return GenerateCredentialOutput(**response.json())

    @legacy_model_argument(GetModelMetadataFromCredentialInput)
    def get_model_metadata_from_credential(self, credential: str) -> GetModelMetadataFromCredentialOutput:
        """Get the model a credential was generated with.

        Useful to tell whether a credential stored some time ago still matches a model the
        service offers today.

        Args:
            credential: The credential to inspect

        Returns:
            GetModelMetadataFromCredentialOutput: The model behind the credential

        Raises:
            FormValidationError: If the credential is not a credential

        """
        data_model = GetModelMetadataFromCredentialInput(credential=credential)
        response = self._post(
            endpoint=DasfaceEndpoints.MODELS_METADATA_FROM_CREDENTIAL.value,
            json_={"credential": data_model.credential},
        )
        return GetModelMetadataFromCredentialOutput(**response.json())

    @legacy_model_argument(VerifyPhotoInput)
    def verify_photo(
        self,
        anchor_image: str | bytes,
        target_image: str | bytes,
        mode: str | None = None,
    ) -> VerificationOutput:
        """Compare two photos and report how confident the service is that they match.

        Args:
            anchor_image: The reference photo, as a path or as bytes
            target_image: The photo to evaluate, as a path or as bytes
            mode: The model mode to use. The service picks its default when omitted

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            FaceNotFoundError: If either photo holds no face
            MoreThanOneFaceError: If either photo holds more than one
            FaceAlignmentError: If a face's key points could not be located
            FormValidationError: If a photo cannot be read

        """
        data_model = VerifyPhotoInput(anchor_image=anchor_image, target_image=target_image, mode=mode)
        body = {
            "anchorImage": encode_base64(data_model.anchor_image),
            "targetImage": encode_base64(data_model.target_image),
        }
        if data_model.mode is not None:
            body["mode"] = data_model.mode

        response = self._post(endpoint=DasfaceEndpoints.VERIFICATION_PHOTO.value, json_=body)
        return VerificationOutput(**response.json())

    @legacy_model_argument(VerifyVideoInput)
    def verify_video(self, anchor_image: str | bytes, target_video: str | bytes) -> VerificationOutput:
        """Compare a photo against the face in a video.

        Args:
            anchor_image: The reference photo, as a path or as bytes
            target_video: The video to evaluate, as a path or as bytes

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            FaceNotFoundError: If no face is found
            ZeroLengthVideoError: If the video is empty or corrupted
            NotEnoughVideoDataError: If the video holds too few usable frames

        """
        data_model = VerifyVideoInput(anchor_image=anchor_image, target_video=target_video)
        response = self._post(
            endpoint=DasfaceEndpoints.VERIFICATION_VIDEO.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetVideo": encode_base64(data_model.target_video),
            },
        )
        return VerificationOutput(**response.json())

    @legacy_model_argument(VerifyCredentialInput)
    def verify_credential(self, anchor_image: str | bytes, target_credential: str) -> VerificationOutput:
        """Compare a photo against a stored credential.

        This is the usual verification: the credential was generated once at enrolment, and
        every later check compares a fresh photo against it without needing the original.

        Args:
            anchor_image: The photo, as a path or as bytes
            target_credential: The credential to compare it with

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            InvalidCredentialError: If the credential cannot be read
            ObsoleteCredentialModelError: If it came from a model the service has dropped
            FaceNotFoundError: If the photo holds no face

        """
        data_model = VerifyCredentialInput(anchor_image=anchor_image, target_credential=target_credential)
        response = self._post(
            endpoint=DasfaceEndpoints.VERIFICATION_CREDENTIAL.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetCredential": data_model.target_credential,
            },
        )
        return VerificationOutput(**response.json())

    @legacy_model_argument(PhotoAuthenticityInput)
    def check_photo_authenticity(self, image: str | bytes) -> PhotoAuthenticityOutput:
        """Check whether a selfie is a genuine capture rather than a photo of a screen or print.

        The face has to fill enough of the frame: a small one is rejected with
        FaceTooSmallForIasError rather than scored low.

        Args:
            image: The selfie to analyse, as a path or as bytes

        Returns:
            PhotoAuthenticityOutput: The confidence, from 0 to 1

        Raises:
            FaceTooSmallForIasError: If the face is too small to analyse
            FaceNotFoundError: If the photo holds no face
            MoreThanOneFaceError: If it holds more than one

        """
        data_model = PhotoAuthenticityInput(image=image)
        response = self._post(
            endpoint=DasfaceEndpoints.AUTHENTICITY_PHOTO.value,
            json_={"targetImage": encode_base64(data_model.image)},
        )
        return PhotoAuthenticityOutput(**response.json())

    @legacy_model_argument(VideoAuthenticityInput)
    def check_video_authenticity(self, anchor_image: str | bytes, target_video: str | bytes) -> VideoAuthenticityOutput:
        """Check whether a video is a genuine recording, and of the expected person.

        Answers both questions at once, and they are independent: a genuine recording of
        somebody else scores high on authenticity and low on similarity.

        Args:
            anchor_image: The photo of the expected person, as a path or as bytes
            target_video: The video to analyse, as a path or as bytes

        Returns:
            VideoAuthenticityOutput: The authenticity and the similarity, each from 0 to 1

        Raises:
            FaceTooSmallForIasError: If a face is too small to analyse
            ZeroLengthVideoError: If the video is empty or corrupted
            VideoExtractionError: If the video cannot be decoded
            NotEnoughVideoDataError: If it holds too few usable frames

        """
        data_model = VideoAuthenticityInput(anchor_image=anchor_image, target_video=target_video)
        response = self._post(
            endpoint=DasfaceEndpoints.AUTHENTICITY_VIDEO_PHOTO.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetVideo": encode_base64(data_model.target_video),
            },
        )
        return VideoAuthenticityOutput(**response.json())

    @legacy_model_argument(SequentialChallengeInput)
    def generate_sequential_challenge(
        self,
        length: int | None = None,
        expiration: int | None = None,
    ) -> SequentialChallengeOutput:
        """Generate a liveness challenge: a sequence of actions for the subject to perform.

        The point of a challenge is that the recording cannot have been prepared in advance,
        since the actions are only known once the challenge is issued. Show the actions to
        the subject, record them, and send the recording back to
        `analyse_challenge_response` together with this token.

        Args:
            length: How many actions to ask for, from 1 to 6. The service defaults to 2
            expiration: How long the challenge stays valid, in seconds, from 300 to 1800.
                The service defaults to 1800

        Returns:
            SequentialChallengeOutput: The token to pass on, and the actions to prompt for

        Raises:
            FormValidationError: If the length or the expiration is out of range

        """
        data_model = SequentialChallengeInput(length=length, expiration=expiration)
        body = {
            key: value
            for key, value in (("length", data_model.length), ("expiration", data_model.expiration))
            if value is not None
        }

        response = self._post(endpoint=DasfaceEndpoints.CHALLENGES_GENERATION_SEQUENTIAL.value, json_=body)
        return self._read_challenge(response)

    def _read_challenge(self, response: Response) -> SequentialChallengeOutput:
        """Read a challenge out of the JWS token the service answers with.

        The signature is not checked. It is not this client's to check: the token is signed
        for the service to verify when the recording comes back, and the key is not
        published. The payload is read only to save every caller writing the same base64
        split, and the token is passed on exactly as it arrived.
        """
        token = response.text.strip()
        try:
            payload = token.split(".")[1]
            challenge = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
            actions = [
                ChallengeAction(
                    name=action["name"],
                    action_class=action["class"],
                    parameters=action.get("parameters") or {},
                )
                for action in challenge["challenge"]["actions"]
            ]
            return SequentialChallengeOutput(
                token=token,
                id=challenge["id"],
                timestamp=challenge["timestamp"],
                expires=challenge["expires"],
                actions=actions,
            )
        except (IndexError, KeyError, TypeError, ValueError, binascii.Error):
            # A 200 whose token cannot be read is the service breaking its own contract.
            self._raise_server_error(response)
            raise

    @legacy_model_argument(ChallengeAnalysisInput)
    def analyse_challenge_response(
        self,
        token: str,
        annotations: str | bytes,
        anchor_image: str | bytes,
        target_video: str | bytes,
    ) -> ChallengeAnalysisOutput:
        """Analyse the recording of a challenge against the photo of the expected person.

        One figure answers all of it: whether the recording is genuine, whether it performs
        the challenge that was issued, and whether it is the right person.

        Unlike every other endpoint here, this one reports what went wrong inside a
        successful response. A confidence of `None` means the analysis could not be
        completed, and the `errors` of the result say why.

        Args:
            token: The token from `generate_sequential_challenge`, unchanged
            annotations: The SDK's WebVTT annotations, as a path or as bytes. A `str` is read
                as a path, so pass in-memory text as `text.encode()`
            anchor_image: The photo of the expected person, as a path or as bytes
            target_video: The recording of the challenge, as a path or as bytes

        Returns:
            ChallengeAnalysisOutput: The confidence, or `None` with the errors behind it

        Raises:
            ExpiredOrInvalidChallengeError: If the challenge is no longer valid
            FormValidationError: If the token, the annotations or a media file cannot be read

        """
        data_model = ChallengeAnalysisInput(
            token=token,
            annotations=annotations,
            anchor_image=anchor_image,
            target_video=target_video,
        )
        response = self._post(
            endpoint=DasfaceEndpoints.CHALLENGES_ANALYSIS_VIDEO_PHOTO.value,
            json_={
                "token": data_model.token,
                "annotations": encode_base64(data_model.annotations),
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetVideo": encode_base64(data_model.target_video),
            },
        )
        payload = response.json()
        return ChallengeAnalysisOutput(
            confidence=payload.get("confidence"),
            errors=[ChallengeError(code=code, message=message) for code, message in payload.get("errors") or []],
        )
