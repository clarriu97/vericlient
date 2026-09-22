"""Implementation of the client for the das-Face service."""

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.dasface.endpoints import DasfaceEndpoints
from vericlient.dasface.exceptions import (
    DasfaceApiError,
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
    GenerateCredentialInput,
    GenerateCredentialOutput,
    GetModelMetadataFromCredentialInput,
    GetModelMetadataFromCredentialOutput,
    ModelsOutput,
    PhotoAuthenticityInput,
    PhotoAuthenticityOutput,
    VerificationOutput,
    VerifyCredentialInput,
    VerifyPhotoInput,
    VerifyVideoInput,
    VideoAuthenticityInput,
    VideoAuthenticityOutput,
)
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

        # One code covers every malformed input, and its message is the only thing that says
        # which, so it is passed through rather than swallowed.
        if code == "FormValidationError":
            raise FormValidationError(payload.get("message"))

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

    def generate_credential(self, data_model: GenerateCredentialInput) -> GenerateCredentialOutput:
        """Generate a credential from a photo.

        A credential is the biometric representation of a face, and what gets stored and
        compared later. With no `hash` and `mode` the service picks its current default
        model, which is what you want unless you are pinning one deliberately.

        Args:
            data_model: The photo, and optionally the model to use

        Returns:
            GenerateCredentialOutput: The credential and the model behind it

        Raises:
            FaceTooSmallForIasError: If the face is too small to analyse
            UnknownHashAndModeError: If no model matches that hash and mode
            FormValidationError: If the photo cannot be read

        """
        if data_model.hash:
            endpoint = DasfaceEndpoints.MODEL_CREDENTIAL_PHOTO.value.replace("<hash>", data_model.hash)
            endpoint = endpoint.replace("<mode>", data_model.mode)
        else:
            endpoint = DasfaceEndpoints.DEFAULT_CREDENTIAL_PHOTO.value

        response = self._post(
            endpoint=endpoint,
            json_={"targetImage": encode_base64(data_model.image)},
        )
        return GenerateCredentialOutput(**response.json())

    def get_model_metadata_from_credential(
        self,
        data_model: GetModelMetadataFromCredentialInput,
    ) -> GetModelMetadataFromCredentialOutput:
        """Get the model a credential was generated with.

        Useful to tell whether a credential stored some time ago still matches a model the
        service offers today.

        Args:
            data_model: The credential to inspect

        Returns:
            GetModelMetadataFromCredentialOutput: The model behind the credential

        Raises:
            FormValidationError: If the credential is not a credential

        """
        response = self._post(
            endpoint=DasfaceEndpoints.MODELS_METADATA_FROM_CREDENTIAL.value,
            json_={"credential": data_model.credential},
        )
        return GetModelMetadataFromCredentialOutput(**response.json())

    def verify_photo(self, data_model: VerifyPhotoInput) -> VerificationOutput:
        """Compare two photos and report how confident the service is that they match.

        Args:
            data_model: The reference photo, the photo to evaluate, and optionally a mode

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            FaceNotFoundError: If either photo holds no face
            MoreThanOneFaceError: If either photo holds more than one
            FaceAlignmentError: If a face's key points could not be located
            FormValidationError: If a photo cannot be read

        """
        body = {
            "anchorImage": encode_base64(data_model.anchor_image),
            "targetImage": encode_base64(data_model.target_image),
        }
        if data_model.mode is not None:
            body["mode"] = data_model.mode

        response = self._post(endpoint=DasfaceEndpoints.VERIFICATION_PHOTO.value, json_=body)
        return VerificationOutput(**response.json())

    def verify_video(self, data_model: VerifyVideoInput) -> VerificationOutput:
        """Compare a photo against the face in a video.

        Args:
            data_model: The reference photo and the video to evaluate

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            FaceNotFoundError: If no face is found
            ZeroLengthVideoError: If the video is empty or corrupted
            NotEnoughVideoDataError: If the video holds too few usable frames

        """
        response = self._post(
            endpoint=DasfaceEndpoints.VERIFICATION_VIDEO.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetVideo": encode_base64(data_model.target_video),
            },
        )
        return VerificationOutput(**response.json())

    def verify_credential(self, data_model: VerifyCredentialInput) -> VerificationOutput:
        """Compare a photo against a stored credential.

        This is the usual verification: the credential was generated once at enrolment, and
        every later check compares a fresh photo against it without needing the original.

        Args:
            data_model: The photo and the credential to compare it with

        Returns:
            VerificationOutput: The confidence, from 0 to 1

        Raises:
            InvalidCredentialError: If the credential cannot be read
            ObsoleteCredentialModelError: If it came from a model the service has dropped
            FaceNotFoundError: If the photo holds no face

        """
        response = self._post(
            endpoint=DasfaceEndpoints.VERIFICATION_CREDENTIAL.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetCredential": data_model.target_credential,
            },
        )
        return VerificationOutput(**response.json())

    def check_photo_authenticity(self, data_model: PhotoAuthenticityInput) -> PhotoAuthenticityOutput:
        """Check whether a selfie is a genuine capture rather than a photo of a screen or print.

        The face has to fill enough of the frame: a small one is rejected with
        FaceTooSmallForIasError rather than scored low.

        Args:
            data_model: The selfie to analyse

        Returns:
            PhotoAuthenticityOutput: The confidence, from 0 to 1

        Raises:
            FaceTooSmallForIasError: If the face is too small to analyse
            FaceNotFoundError: If the photo holds no face
            MoreThanOneFaceError: If it holds more than one

        """
        response = self._post(
            endpoint=DasfaceEndpoints.AUTHENTICITY_PHOTO.value,
            json_={"targetImage": encode_base64(data_model.image)},
        )
        return PhotoAuthenticityOutput(**response.json())

    def check_video_authenticity(self, data_model: VideoAuthenticityInput) -> VideoAuthenticityOutput:
        """Check whether a video is a genuine recording, and of the expected person.

        Answers both questions at once, and they are independent: a genuine recording of
        somebody else scores high on authenticity and low on similarity.

        Args:
            data_model: The photo of the expected person and the video to analyse

        Returns:
            VideoAuthenticityOutput: The authenticity and the similarity, each from 0 to 1

        Raises:
            FaceTooSmallForIasError: If a face is too small to analyse
            ZeroLengthVideoError: If the video is empty or corrupted
            VideoExtractionError: If the video cannot be decoded
            NotEnoughVideoDataError: If it holds too few usable frames

        """
        response = self._post(
            endpoint=DasfaceEndpoints.AUTHENTICITY_VIDEO_PHOTO.value,
            json_={
                "anchorImage": encode_base64(data_model.anchor_image),
                "targetVideo": encode_base64(data_model.target_video),
            },
        )
        return VideoAuthenticityOutput(**response.json())
