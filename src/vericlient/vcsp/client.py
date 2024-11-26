"""Implementation of the client for the VCSP service."""
from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.vcsp.endpoints import VcspEndpoints
from vericlient.vcsp.models import (
    EnrollmentInput,
    EnrollmentOutput,
    DeleteSubjectInput,
    DeleteCredentialInput,
    GetAccountInput,
    GetAccountOutput,
    GetCredentialInput,
    GetCredentialOutput,
)
from vericlient.vcsp.exceptions import (
    EmptyFileError,
    InvalidClaimsError,
    InvalidAssuranceError,
    InvalidTagsError,
    InvalidCredentialConfigurationUrnError,
    InvalidAssuranceMethodUrnError,
    InsufficientQualityError,
    InvalidAudioFormatError,
    InvalidSnrError,
    CredentialConfigurationUrnAlreadyAssignedError,
    VoiceDurationIsNotEnoughError,
    FaceAlignmentError,
    FaceNotFoundError,
    FaceTooSmallError,
    MoreThanOneFaceError,
    AssuranceValidationError,
    AccountNotFoundError,
    CredentialNotFoundError,
)
from vericlient.utils import get_virtual_file


class VcspClient(Client):
    """Class to interact with the VCSP API."""

    def __init__(
            self,
            api: str = APIs.VCSP.value,
            apikey: str | None = None,
            timeout: int | None = None,
            environment: str | None = None,
            location: str | None = None,
            url: str | None = None,
            headers: dict | None = None,
    ) -> None:
        """Create the VcspClient class.

        Args:
            api: The API to use
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        super().__init__(
            api=api,
            apikey=apikey,
            timeout=timeout,
            environment=environment,
            location=location,
            url=url,
            headers=headers,
        )
        self._exceptions = {
            "empty_file": EmptyFileError,
            "invalid_claims": InvalidClaimsError,
            "invalid_assurance": InvalidAssuranceError,
            "invalid_tags": InvalidTagsError,
            "invalid_credential_configuration_urn": InvalidCredentialConfigurationUrnError,
            "invalid_assurance_method_urn": InvalidAssuranceMethodUrnError,
            "credential_configuration_urn_already_assigned": CredentialConfigurationUrnAlreadyAssignedError,
            "invalid_audio_format": InvalidAudioFormatError,
            "invalid_signal_to_noise_ratio": InvalidSnrError,
            "voice_duration_is_not_enough": VoiceDurationIsNotEnoughError,
            "insufficient_quality": InsufficientQualityError,
            "face_not_found": FaceNotFoundError,
            "more_than_one_face": MoreThanOneFaceError,
            "face_too_small_for_ias": FaceTooSmallError,
            "face_alignment": FaceAlignmentError,
            "assurance_validation_error": AssuranceValidationError,
            "account_not_found": AccountNotFoundError,
            "credential_not_found": CredentialNotFoundError,
        }

    def alive(self) -> bool:
        """Check if the service is alive.

        Returns
            bool: True if the service is alive, False otherwise

        """
        response = self._get(endpoint=VcspEndpoints.ALIVE.value)
        accepted_status_code = 204
        return response.status_code == accepted_status_code

    def _handle_error_response(self, response: Response) -> None:
        """Handle error responses from the API."""
        response_json = response.json()

        exception = response_json.get("error")
        if not exception or exception not in self._exceptions.keys():
            self._raise_server_error(response)

        handler = self._exceptions[exception]
        raise handler()

    def enroll_subject(self, data_model: EnrollmentInput) -> EnrollmentOutput:
        """Enroll a subject.

        Args:
            data_model: The input to enroll the subject

        Returns:
            EnrollmentOutput: The output of the enrollment

        Raises:
            EmptyFileError: If the file is empty
            InvalidClaimsError: If the claims are invalid
            InvalidAssuranceError: If the assurance is invalid
            InvalidTagsError: If the tags are invalid
            InvalidCredentialConfigurationUrnError: If the credential configuration urn is invalid
            InvalidAssuranceMethodUrnError: If the assurance method urn is invalid
            CredentialConfigurationUrnAlreadyAssignedError: If the credential configuration urn is already assigned
            InvalidAudioFormatError: If the audio format is invalid
            InvalidSnrError: If the signal noise ratio is invalid
            VoiceDurationIsNotEnoughError: If the voice duration is not enough
            InsufficientQualityError: If the quality is insufficient
            FaceAlignmentError: If the face is not aligned
            FaceNotFoundError: If the face is not found
            FaceTooSmallError: If the face is too small
            MoreThanOneFaceError: If there is more than one face
            AssuranceValidationError: If the assurance is invalid
        """
        endpoint = VcspEndpoints.ENROLLMENTS.value
        sample = get_virtual_file(data_model.sample)
        files = {"sample": sample}
        applicant = data_model.applicant.model_dump()
        applicant = {k: v for k, v in applicant.items() if v is not None}
        data = {"applicant": applicant}
        response = self._post(
            endpoint=endpoint,
            files=files,
            data=data,
        )
        return EnrollmentOutput(status_code=response.status_code, **response.json())

    def delete_subject(self, data_model: DeleteSubjectInput) -> None:
        """Delete a subject.

        Args:
            data_model: The input to delete the subject

        """
        endpoint = VcspEndpoints.ACCOUNTS.value.replace("<subject_id>", data_model.subject_id)
        self._delete(endpoint=endpoint)

    def delete_credential(self, data_model: DeleteCredentialInput) -> None:
        """Delete a credential.

        Args:
            data_model: The input to delete the credential

        """
        endpoint = VcspEndpoints.CREDENTIAL_ID.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        self._delete(endpoint=endpoint)

    def get_account(self, data_model: GetAccountInput) -> GetAccountOutput:
        """Get an account.

        Args:
            data_model: The input to get the account

        Returns:
            GetAccountOutput: The output of the account

        Raises:
            AccountNotFoundError: If the account is not found

        """
        endpoint = VcspEndpoints.ACCOUNTS.value.replace("<subject_id>", data_model.subject_id)
        response = self._get(endpoint=endpoint)
        return GetAccountOutput(status_code=response.status_code, **response.json())

    def get_credential(self, data_model: GetCredentialInput) -> GetCredentialOutput:
        """Get a credential.

        Args:
            data_model: The input to get the credential

        Returns:
            GetCredentialOutput: The output of the credential

        Raises:
            CredentialNotFoundError: If the credential is not found
            AccountNotFoundError: If the account is not found

        """
        endpoint = VcspEndpoints.CREDENTIAL_ID.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        response = self._get(endpoint=endpoint)
        return GetCredentialOutput(status_code=response.status_code, **response.json())
