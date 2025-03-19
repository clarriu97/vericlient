"""Implementation of the client for the VCSP service."""
from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.vcsp.endpoints import VcspEndpoints
from vericlient.vcsp.exceptions import (
    AccountNotFoundError,
    AssuranceValidationError,
    CredentialConfigurationUrnAlreadyAssignedError,
    CredentialNotFoundError,
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
    VoiceDurationIsNotEnoughError,
)
from vericlient.vcsp.models import (
    AssuranceMethodInput,
    AssuranceMethodOutput,
    AssuranceMethodsOutput,
    CredentialConfigurationsOutput,
)


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
        if not exception or exception not in self._exceptions:
            self._raise_server_error(response)

        handler = self._exceptions[exception]
        raise handler()

    def get_credential_configurations(self) -> CredentialConfigurationsOutput:
        """Get all credential configurations.

        Returns:
            CredentialConfigurationsOutput: The output of the credential configurations

        """
        endpoint = VcspEndpoints.CREDENTIAL_CONFIGURATIONS.value
        response = self._get(endpoint=endpoint)
        return CredentialConfigurationsOutput(
            status_code=response.status_code,
            credential_configurations=response.json(),
        )

    def get_assurance_methods(self) -> AssuranceMethodsOutput:
        """Get all assurance methods.

        Returns:
            AssuranceMethodsOutput: The output of the assurance methods

        """
        endpoint = VcspEndpoints.ASSURANCE_METHODS.value
        response = self._get(endpoint=endpoint)
        return AssuranceMethodsOutput(
            status_code=response.status_code,
            assurance_methods=response.json(),
        )

    def get_assurance_method(self, data_model: AssuranceMethodInput) -> AssuranceMethodOutput:
        """Get an assurance method.

        Args:
            data_model: The input to get the assurance method

        Returns:
            AssuranceMethodOutput: The output of the assurance method

        """
        endpoint = VcspEndpoints.ASSURANCE_METHOD_URN.value.replace("<urn>", data_model.urn)
        response = self._get(endpoint=endpoint)
        return AssuranceMethodOutput(status_code=response.status_code, **response.json())
