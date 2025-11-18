"""Implementation of the client for the VCSP service."""
import json
import mimetypes
import os

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.vcsp.endpoints import VcspEndpoints
from vericlient.vcsp.exceptions import (
    AccountNotFoundError,
    AssuranceMethodNotFoundError,
    AssuranceValidationError,
    CredentialConfigurationUrnAlreadyAssignedError,
    CredentialNotFoundError,
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
    AssuranceMethodInput,
    AssuranceMethodOutput,
    AssuranceMethodsOutput,
    CreateGroupInput,
    CreateGroupOutput,
    CreateTagsInput,
    CreateTagsOutput,
    CredentialConfigurationsOutput,
    DeleteAccountInput,
    DeleteCredentialInput,
    DeleteGroupInput,
    DeleteTagInput,
    EnrollmentInput,
    EnrollmentOutput,
    GetAccountInput,
    GetAccountOutput,
    GetCredentialInput,
    GetCredentialOutput,
    GetCredentialsInput,
    GetCredentialsOutput,
    GetGroupInput,
    GetGroupMembersInput,
    GetGroupMembersOutput,
    GetGroupOutput,
    GetGroupsInput,
    GetGroupsOutput,
    GetTagsOutput,
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
            "invalid_signal_noise_ratio": InvalidSnrError,
            "voice_duration_is_not_enough": VoiceDurationIsNotEnoughError,
            "insufficient_quality": InsufficientQualityError,
            "face_not_found": FaceNotFoundError,
            "more_than_one_face": MoreThanOneFaceError,
            "face_too_small_for_ias": FaceTooSmallError,
            "face_alignment": FaceAlignmentError,
            "assurance_validation_error": AssuranceValidationError,
            "assurance_method_not_found": AssuranceMethodNotFoundError,
            "account_not_found": AccountNotFoundError,
            "credential_not_found": CredentialNotFoundError,
            "request_validation_error": RequestValidationError,
            "unsupported_media_type": UnsupportedMediaTypeError,
            "groups_limit_exceeded": GroupsLimitExceededError,
            "enrollments_limit_exceeded": EnrollmentsLimitExceededError,
            "group_already_exists": GroupAlreadyExistsError,
            "group_not_found": GroupNotFoundError,
            "tags_limit_exceeded": TagsLimitExceededError,
            "tag_list_empty": TagListEmptyError,
            "tags_already_exist": TagAlreadyExistsError,
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

        if exception == "request_validation_error":
            raise RequestValidationError(response_json["details"])

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

    def get_assurance_method_info(self, data_model: AssuranceMethodInput) -> AssuranceMethodOutput:
        """Get an assurance method.

        Args:
            data_model: The input to get the assurance method

        Returns:
            AssuranceMethodOutput: The output of the assurance method

        """
        endpoint = VcspEndpoints.ASSURANCE_METHOD_URN.value.replace("<urn>", data_model.urn)
        response = self._get(endpoint=endpoint)
        return AssuranceMethodOutput(status_code=response.status_code, **response.json())

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
            RequestValidationError: If the request is invalid
            UnsupportedMediaTypeError: If the media type is not supported

        """
        endpoint = VcspEndpoints.ENROLLMENTS.value
        sample = self._get_sample(data_model.sample)
        files = {"sample": sample}
        data = {"applicant": json.dumps(data_model.applicant.model_dump(exclude_none=True))}
        response = self._post(
            endpoint=endpoint,
            files=files,
            data=data,
        )
        return EnrollmentOutput(status_code=response.status_code, **response.json())

    def _get_sample(self, sample: str | bytes) -> tuple[str, bytes, str]:
        """Given a sample, return the filename, the file and the content type."""
        if isinstance(sample, str):
            filename = os.path.basename(sample)
            with open(sample, "rb") as f:
                file = f.read()
            content_type = mimetypes.guess_type(sample)[0]
        if isinstance(sample, bytes):
            filename = "sample"
            file = sample
            content_type = mimetypes.guess_type(sample)[0]
        return filename, file, content_type

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

    def delete_account(self, data_model: DeleteAccountInput) -> None:
        """Delete an account.

        Args:
            data_model: The input to delete the account

        Raises:
            AccountNotFoundError: If the account is not found

        """
        endpoint = VcspEndpoints.ACCOUNTS.value.replace("<subject_id>", data_model.subject_id)
        self._delete(endpoint=endpoint)

    def get_all_subject_credentials(self, data_model: GetCredentialsInput) -> GetCredentialsOutput:
        """Get all credentials for a subject.

        Args:
            data_model: The input to get all credentials for the subject

        Returns:
            GetCredentialsOutput: The output of the credentials

        Raises:
            AccountNotFoundError: If the account is not found

        """
        endpoint = VcspEndpoints.CREDENTIALS.value.replace("<subject_id>", data_model.subject_id)
        response = self._get(endpoint=endpoint)
        return GetCredentialsOutput(credentials=response.json(), status_code=response.status_code)

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

    def delete_credential(self, data_model: DeleteCredentialInput) -> None:
        """Delete a credential.

        Args:
            data_model: The input to delete the credential

        """
        endpoint = VcspEndpoints.CREDENTIAL_ID.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        self._delete(endpoint=endpoint)

    def create_tags(self, data_model: CreateTagsInput) -> CreateTagsOutput:
        """Create tags.

        Args:
            data_model: The input to create the tags

        Returns:
            CreateTagsOutput: The output of the tags creation

        Raises:
            TagsLimitExceededError: If the tag limit is exceeded
            TagAlreadyExistsError: If the tag already exists
            TagListEmptyError: If the tag list is empty

        """
        endpoint = VcspEndpoints.TAGS.value
        response = self._post(endpoint=endpoint, json_=data_model.model_dump())
        return CreateTagsOutput(status_code=response.status_code, **response.json())

    def get_tags(self) -> GetTagsOutput:
        """Get tags.

        Args:
            data_model: The input to get the tags

        Returns:
            GetTagsOutput: The output of the tags

        """
        endpoint = VcspEndpoints.TAGS.value
        response = self._get(endpoint=endpoint)
        return GetTagsOutput(status_code=response.status_code, **response.json())

    def delete_tag(self, data_model: DeleteTagInput) -> None:
        """Delete a tag.

        Args:
            data_model: The input to delete the tag

        Raises:
            InvalidTagsError: If the tag is invalid

        """
        endpoint = VcspEndpoints.TAGS_NAME.value.replace("<tag_name>", data_model.name)
        self._delete(endpoint=endpoint)

    def create_group(self, data_model: CreateGroupInput) -> CreateGroupOutput:
        """Create a group.

        Args:
            data_model: The input to create the group

        Returns:
            CreateGroupOutput: The output of the group creation

        Raises:
            GroupsLimitExceededError: If the group limit is exceeded
            GroupAlreadyExistsError: If the group already exists
            InvalidCredentialConfigurationUrnError: If the credential configuration urn is invalid

        """
        endpoint = VcspEndpoints.GROUPS.value
        response = self._post(endpoint=endpoint, json_=data_model.model_dump(exclude_none=True))
        return CreateGroupOutput(status_code=response.status_code, **response.json())

    def get_groups(self, data_model: GetGroupsInput) -> GetGroupsOutput:
        """Get all groups.

        Args:
            data_model: The input to get the groups

        Returns:
            GetGroupsOutput: The output of the groups

        """
        endpoint = VcspEndpoints.GROUPS.value
        endpoint = endpoint + f"?size={data_model.size}&page={data_model.page}"
        response = self._get(endpoint=endpoint)
        items = response.json()["items"]
        total = response.json()["total"]
        page = response.json()["page"]
        size = response.json()["size"]
        pages = response.json()["pages"]
        return GetGroupsOutput(
            status_code=response.status_code,
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    def get_group(self, data_model: GetGroupInput) -> GetGroupOutput:
        """Get a group.

        Args:
            data_model: The input to get the group

        Returns:
            GetGroupOutput: The output of the group

        Raises:
            GroupNotFoundError: If the group is not found

        """
        endpoint = VcspEndpoints.GROUP_NAME.value.replace("<group_name>", data_model.name)
        response = self._get(endpoint=endpoint)
        return GetGroupOutput(status_code=response.status_code, **response.json())

    def delete_group(self, data_model: DeleteGroupInput) -> None:
        """Delete a group.

        Args:
            data_model: The input to delete the group

        Raises:
            GroupNotFoundError: If the group is not found

        """
        endpoint = VcspEndpoints.GROUP_NAME.value.replace("<group_name>", data_model.name)
        self._delete(endpoint=endpoint)

    def get_group_members(self, data_model: GetGroupMembersInput) -> GetGroupMembersOutput:
        """Get the members of a group.

        Args:
            data_model: The input to get the members of the group

        Returns:
            GetGroupMembersOutput: The output of the group members

        Raises:
            GroupNotFoundError: If the group is not found

        """
        endpoint = VcspEndpoints.GROUP_MEMBERS.value.replace("<group_name>", data_model.name)
        response = self._get(endpoint=endpoint)
        return GetGroupMembersOutput(status_code=response.status_code, **response.json())
