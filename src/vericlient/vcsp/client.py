"""Implementation of the client for the VCSP service."""

import json
import mimetypes
import os
import time

from requests.models import Response

from vericlient.apis import APIs
from vericlient.client import Client
from vericlient.deprecation import legacy_model_argument
from vericlient.utils import DEFAULT_CONTENT_TYPE, get_virtual_file, guess_content_type
from vericlient.vcsp.batch import build_batch_archive, sample_filename
from vericlient.vcsp.endpoints import VcspEndpoints
from vericlient.vcsp.exceptions import (
    AccountNotFoundError,
    AssuranceMethodNotFoundError,
    AssuranceValidationError,
    ClusteringNotSupportedError,
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
    InvalidBatchFileError,
    InvalidClaimsError,
    InvalidCredentialConfigurationUrnError,
    InvalidSnrError,
    InvalidTagsError,
    MoreThanOneFaceError,
    RequestValidationError,
    TagAlreadyExistsError,
    TagListEmptyError,
    TagsLimitExceededError,
    TaskNotFoundError,
    UnsupportedMediaTypeError,
    VoiceDurationIsNotEnoughError,
)
from vericlient.vcsp.models import (
    Applicant,
    AssuranceMethodInput,
    AssuranceMethodOutput,
    AssuranceMethodsOutput,
    BatchApplicant,
    BatchEnrollmentInput,
    BatchEnrollmentOutput,
    ClusteringInput,
    CreateGroupInput,
    CreateGroupOutput,
    CreateTagsInput,
    CreateTagsOutput,
    CredentialConfigurationInput,
    CredentialConfigurationOutput,
    CredentialConfigurationsOutput,
    DeleteAccountInput,
    DeleteCredentialInput,
    DeleteCredentialsInput,
    DeleteGroupInput,
    DeleteTagInput,
    EnrollmentInput,
    EnrollmentOutput,
    GetAccountInput,
    GetAccountOutput,
    GetCredentialInput,
    GetCredentialOutput,
    GetCredentialSampleInput,
    GetCredentialSampleOutput,
    GetCredentialsInput,
    GetCredentialsOutput,
    GetGroupInput,
    GetGroupMembersInput,
    GetGroupMembersOutput,
    GetGroupOutput,
    GetGroupsInput,
    GetGroupsOutput,
    GetTagsOutput,
    GetTaskResultOutput,
    GetTasksOutput,
    GroupClaimant,
    GroupMembershipSource,
    ListCredentialsInput,
    ListCredentialsOutput,
    MatchingInput,
    MatchingOutput,
    ModifyCredentialTagsInput,
    ModifyGroupInput,
    SubjectClaimant,
    TaskCreatedOutput,
    TaskInput,
    TaskOutput,
)


class VcspClient(Client):
    """Class to interact with the VCSP API."""

    def __init__(
        self,
        apikey: str | None = None,
        timeout: int | None = None,
        environment: str | None = None,
        location: str | None = None,
        url: str | None = None,
        headers: dict | None = None,
    ) -> None:
        """Create the VcspClient class.

        Args:
            apikey: The API key to use
            timeout: The timeout to use in the requests
            environment: The environment to use
            location: The location to use
            url: The URL to use in case of a custom target
            headers: The headers to be used in the requests

        """
        super().__init__(
            api=APIs.VCSP,
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
            "task_not_found": TaskNotFoundError,
            "invalid_batch_file": InvalidBatchFileError,
            "clustering_not_supported": ClusteringNotSupportedError,
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
        response_json = self._error_payload(response)

        exception = response_json.get("error")
        if not exception or exception not in self._exceptions:
            self._raise_server_error(response)

        if exception == "request_validation_error":
            raise RequestValidationError(response_json["details"])

        handler = self._exceptions[exception]
        raise handler()

    @legacy_model_argument(ListCredentialsInput)
    def list_credentials(
        self,
        credential_configuration_urn: str | None = None,
        tags: list[str] | None = None,
        page: int | None = None,
        size: int | None = None,
    ) -> ListCredentialsOutput:
        """List credentials across the whole system, optionally filtered.

        Unlike `get_all_subject_credentials`, this is not scoped to one account. Deployments
        hold a lot of credentials, so filter and page rather than walking everything.

        Args:
            credential_configuration_urn: Only credentials created with this configuration
            tags: Only credentials carrying these tags
            page: The page to retrieve, starting at 1
            size: How many credentials per page

        Returns:
            ListCredentialsOutput: A page of credentials

        """
        data_model = ListCredentialsInput(
            credential_configuration_urn=credential_configuration_urn,
            tags=tags,
            page=page,
            size=size,
        )
        response = self._get(
            endpoint=VcspEndpoints.ALL_CREDENTIALS.value,
            params=data_model.model_dump(exclude_none=True),
        )
        return ListCredentialsOutput(**response.json())

    @legacy_model_argument(DeleteCredentialsInput)
    def delete_credentials(
        self,
        group_name: str,
        delete_empty_accounts: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Delete every credential in a group.

        Irreversible. The credentials are removed from any other group they belong to, and
        with `delete_empty_accounts` the accounts left holding nothing go too.

        Args:
            group_name: The group whose credentials are deleted
            delete_empty_accounts: Whether to delete an account left with no credentials

        Raises:
            GroupNotFoundError: If no group exists with that name

        """
        data_model = DeleteCredentialsInput(group_name=group_name, delete_empty_accounts=delete_empty_accounts)
        self._delete(
            endpoint=VcspEndpoints.ALL_CREDENTIALS.value,
            json_=data_model.model_dump(),
        )

    @legacy_model_argument(GetCredentialSampleInput)
    def get_credential_sample(
        self,
        credential_id: str,
        subject_id: str,
    ) -> GetCredentialSampleOutput:
        """Get the sample a credential was created from.

        The service answers with the raw bytes rather than JSON, so the media type comes
        from the response header.

        Args:
            credential_id: The credential whose sample to retrieve
            subject_id: The subject the credential belongs to

        Returns:
            GetCredentialSampleOutput: The sample and its media type

        Raises:
            AccountNotFoundError: If the account is not found
            CredentialNotFoundError: If the credential is not found

        """
        data_model = GetCredentialSampleInput(credential_id=credential_id, subject_id=subject_id)
        endpoint = VcspEndpoints.CREDENTIAL_SAMPLE.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        response = self._get(endpoint=endpoint)
        return GetCredentialSampleOutput(
            content=response.content,
            content_type=response.headers.get("content-type", DEFAULT_CONTENT_TYPE),
        )

    @legacy_model_argument(CredentialConfigurationInput)
    def get_credential_configuration(
        self,
        urn: str,
    ) -> CredentialConfigurationOutput:
        """Get one credential configuration, including the schema its claims must satisfy.

        Args:
            urn: The urn of the credential configuration

        Returns:
            CredentialConfigurationOutput: The configuration and its claims schema

        Raises:
            InvalidCredentialConfigurationUrnError: If no configuration exists with that urn

        """
        data_model = CredentialConfigurationInput(urn=urn)
        endpoint = VcspEndpoints.CREDENTIAL_CONFIGURATION_URN.value.replace("<urn>", data_model.urn)
        response = self._get(endpoint=endpoint)
        return CredentialConfigurationOutput(**response.json())

    @legacy_model_argument(BatchEnrollmentInput)
    def enroll_batch(
        self,
        applicants: list[BatchApplicant] | None = None,
        batch_file: str | bytes | None = None,
    ) -> BatchEnrollmentOutput:
        """Enrol several applicants at once.

        The work happens asynchronously. Follow it with `get_task`, or block on
        `wait_for_task`, and collect the outcome with `get_task_result`.

        Pass `applicants` and the client builds the archive the service expects. Neither the
        `applicants.json` name nor the `file://` reference its entries use is documented;
        both were found by reading the service's errors.

        Args:
            applicants: The enrolments to perform
            batch_file: A prepared TAR archive, as a path or as bytes

        Returns:
            BatchEnrollmentOutput: The task the enrolments run under

        Raises:
            InvalidBatchFileError: If the archive is malformed or a sample is missing

        """
        data_model = BatchEnrollmentInput(applicants=applicants, batch_file=batch_file)
        if data_model.batch_file is not None:
            archive = get_virtual_file(data_model.batch_file)
        else:
            entries = [
                (
                    sample_filename(applicant.sample, index, applicant.filename),
                    get_virtual_file(applicant.sample),
                    applicant.applicant.model_dump(exclude_none=True),
                )
                for index, applicant in enumerate(data_model.applicants)
            ]
            archive = build_batch_archive(entries)

        response = self._post(
            endpoint=VcspEndpoints.ENROLLMENTS_BATCH.value,
            files={"batch_file": ("batch.tar", archive, "application/x-tar")},
        )
        return BatchEnrollmentOutput(**response.json())

    def get_tasks(self) -> GetTasksOutput:
        """List the asynchronous tasks the service is still holding.

        Returns:
            GetTasksOutput: The active tasks, paginated

        """
        response = self._get(endpoint=VcspEndpoints.TASKS.value)
        return GetTasksOutput(**response.json())

    @legacy_model_argument(TaskInput)
    def get_task(
        self,
        task_id: str,
    ) -> TaskOutput:
        """Get the state of one asynchronous task.

        Args:
            task_id: The identifier the service returned when the task was created

        Returns:
            TaskOutput: Its status and progress

        Raises:
            TaskNotFoundError: If no task exists with that identifier

        """
        data_model = TaskInput(task_id=task_id)
        endpoint = VcspEndpoints.TASK_ID.value.replace("<task_id>", data_model.task_id)
        response = self._get(endpoint=endpoint)
        return TaskOutput(**response.json())

    @legacy_model_argument(TaskInput)
    def delete_task(
        self,
        task_id: str,
    ) -> None:
        """Delete a task and its result.

        Tasks expire on their own, but a long-running caller is better off tidying up.

        Args:
            task_id: The identifier the service returned when the task was created

        Raises:
            TaskNotFoundError: If no task exists with that identifier

        """
        data_model = TaskInput(task_id=task_id)
        endpoint = VcspEndpoints.TASK_ID.value.replace("<task_id>", data_model.task_id)
        self._delete(endpoint=endpoint)

    @legacy_model_argument(TaskInput)
    def get_task_result(
        self,
        task_id: str,
    ) -> GetTaskResultOutput:
        """Get the outcome of a finished task.

        The shape depends on what created the task, so it comes back as a dictionary.

        Args:
            task_id: The identifier the service returned when the task was created

        Returns:
            GetTaskResultOutput: The outcome, as the service returned it

        Raises:
            TaskNotFoundError: If no task exists with that identifier

        """
        data_model = TaskInput(task_id=task_id)
        endpoint = VcspEndpoints.TASK_RESULT.value.replace("<task_id>", data_model.task_id)
        response = self._get(endpoint=endpoint)
        return GetTaskResultOutput(result=response.json())

    @legacy_model_argument(TaskInput)
    def wait_for_task(
        self,
        task_id: str,
        timeout: float = 300,
        poll_interval: float = 2,
    ) -> TaskOutput:
        """Block until a task finishes, and return its final state.

        Saves every caller writing the same polling loop. It returns on failure as well as on
        success, so check `succeeded` on the result.

        Args:
            task_id: The task to wait for
            timeout: How long to wait, in seconds, before giving up
            poll_interval: How long to sleep between checks, in seconds

        Returns:
            TaskOutput: The task in its final state

        Raises:
            TaskNotFoundError: If no task exists with that identifier
            TimeoutError: If the task has not finished within `timeout`

        """
        deadline = time.monotonic() + timeout
        while True:
            task = self.get_task(task_id=task_id)
            if task.is_finished:
                return task
            if time.monotonic() >= deadline:
                error = f"Task {task_id} did not finish within {timeout} seconds"
                raise TimeoutError(error)
            time.sleep(poll_interval)

    @legacy_model_argument(MatchingInput)
    def match(
        self,
        sample: str | bytes,
        claimant: SubjectClaimant | GroupClaimant,
        sample_processing: dict | None = None,
        content_type: str | None = None,
    ) -> MatchingOutput | TaskCreatedOutput:
        """Match a sample against one subject or against a whole group.

        Pass a `SubjectClaimant` for 1:1 or a `GroupClaimant` for 1:N. Small operations
        answer straight away with a `MatchingOutput`; a large one is accepted and run
        asynchronously, answering with a `TaskCreatedOutput` to follow with `wait_for_task`.

        Args:
            sample: The biometric sample to match, as a path or as bytes
            claimant: What to match it against — a `SubjectClaimant` for 1:1, a `GroupClaimant` for 1:N
            sample_processing: Options for reading the sample, such as `{"nchannel": 1}`
            content_type: The media type to declare for the sample. Inferred when omitted

        Returns:
            MatchingOutput when the service answered directly, TaskCreatedOutput when it
            queued the work

        Raises:
            AccountNotFoundError: If the subject does not exist
            GroupNotFoundError: If the group does not exist
            InvalidAssuranceError: If the assurance does not satisfy its method's schema

        """
        data_model = MatchingInput(
            sample=sample, claimant=claimant, sample_processing=sample_processing, content_type=content_type
        )
        filename, sample, content_type = self._get_sample(data_model.sample, data_model.content_type)
        data = {"claimant": json.dumps(data_model.claimant.model_dump(exclude_none=True))}
        if data_model.sample_processing is not None:
            data["sample_processing"] = json.dumps(data_model.sample_processing)

        response = self._post(
            endpoint=VcspEndpoints.MATCHINGS.value,
            files={"sample": (filename, sample, content_type)},
            data=data,
        )
        accepted = 202
        if response.status_code == accepted:
            return TaskCreatedOutput(**response.json())
        return MatchingOutput(**response.json())

    @legacy_model_argument(ModifyGroupInput)
    def modify_group(
        self,
        name: str,
        action: str,
        from_: GroupMembershipSource | None = None,
        credential_ttl: str | None = None,
        description: str | None = None,
        expired_at: str | None = None,
    ) -> GetGroupOutput | TaskCreatedOutput:
        """Add credentials to a group, remove them, or change the group's own details.

        A small change answers directly with the group; a large population is accepted and
        run asynchronously.

        Args:
            name: The group to modify
            action: `populate`, `remove` or `update_info`
            from_: Which credentials to add or remove. Required for populate and remove, and serialised as `from`, which is a
                reserved word in Python
            credential_ttl: How long added credentials stay in the group, as an ISO 8601 duration such as `P30D`
            description: A new description, for `update_info`
            expired_at: A new retention period, for `update_info`, as an ISO 8601 duration

        Returns:
            GetGroupOutput when the service answered directly, TaskCreatedOutput when it
            queued the work

        Raises:
            GroupNotFoundError: If the group does not exist
            AccountNotFoundError: If one of the subjects does not exist

        """
        data_model = ModifyGroupInput(
            name=name, action=action, from_=from_, credential_ttl=credential_ttl, description=description, expired_at=expired_at
        )
        endpoint = VcspEndpoints.GROUP_NAME.value.replace("<group_name>", data_model.name)
        body = data_model.model_dump(exclude_none=True, by_alias=True, exclude={"name"})
        response = self._patch(endpoint=endpoint, json_=body)
        accepted = 202
        if response.status_code == accepted:
            return TaskCreatedOutput(**response.json())
        return GetGroupOutput(**response.json())

    @legacy_model_argument(ModifyCredentialTagsInput)
    def modify_credential_tags(
        self,
        credential_id: str,
        subject_id: str,
        action: str,
        tags: list[str],
    ) -> GetCredentialOutput:
        """Add or remove tags on one credential.

        The tags have to exist already: create them with `create_tags` first.

        Args:
            credential_id: The credential to change
            subject_id: The subject the credential belongs to
            action: `add` or `remove`
            tags: The tags to add or remove. They must already exist in the system

        Returns:
            GetCredentialOutput: The credential as it now stands

        Raises:
            CredentialNotFoundError: If the credential is not found
            AccountNotFoundError: If the account is not found
            InvalidTagsError: If one of the tags does not exist

        """
        data_model = ModifyCredentialTagsInput(credential_id=credential_id, subject_id=subject_id, action=action, tags=tags)
        endpoint = VcspEndpoints.CREDENTIAL_TAGS.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        response = self._patch(
            endpoint=endpoint,
            json_={"action": data_model.action, "tags": data_model.tags},
        )
        return GetCredentialOutput(**response.json())

    @legacy_model_argument(ClusteringInput)
    def start_clustering(
        self,
        name: str,
        assurance_method_urn: str,
        properties: dict,
    ) -> TaskCreatedOutput:
        """Start a clustering task over a group.

        Only groups of face credentials can be clustered; a voice group is rejected.

        Args:
            name: The group to cluster
            assurance_method_urn: The clustering assurance method to apply
            properties: The values that method requires, such as `{"similarity_threshold": 0.5, "mode": "similarity_based"}`. Note
                the service calls this `properties`, not `assurance` as everywhere else

        Returns:
            TaskCreatedOutput: The task the clustering runs under

        Raises:
            GroupNotFoundError: If the group does not exist
            ClusteringNotSupportedError: If the group does not hold face credentials

        """
        data_model = ClusteringInput(name=name, assurance_method_urn=assurance_method_urn, properties=properties)
        endpoint = VcspEndpoints.GROUP_CLUSTERING.value.replace("<group_name>", data_model.name)
        response = self._post(
            endpoint=endpoint,
            json_={
                "assurance_method_urn": data_model.assurance_method_urn,
                "properties": data_model.properties,
            },
        )
        return TaskCreatedOutput(**response.json())

    def get_credential_configurations(self) -> CredentialConfigurationsOutput:
        """Get all credential configurations.

        Returns:
            CredentialConfigurationsOutput: The output of the credential configurations

        """
        endpoint = VcspEndpoints.CREDENTIAL_CONFIGURATIONS.value
        response = self._get(endpoint=endpoint)
        return CredentialConfigurationsOutput(
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
            assurance_methods=response.json(),
        )

    @legacy_model_argument(AssuranceMethodInput)
    def get_assurance_method_info(
        self,
        urn: str,
    ) -> AssuranceMethodOutput:
        """Get an assurance method.

        Args:
            urn: The urn of the assurance method

        Returns:
            AssuranceMethodOutput: The output of the assurance method

        """
        data_model = AssuranceMethodInput(urn=urn)
        endpoint = VcspEndpoints.ASSURANCE_METHOD_URN.value.replace("<urn>", data_model.urn)
        response = self._get(endpoint=endpoint)
        return AssuranceMethodOutput(**response.json())

    @legacy_model_argument(EnrollmentInput)
    def enroll_subject(
        self,
        sample: str | bytes,
        applicant: Applicant,
        content_type: str | None = None,
    ) -> EnrollmentOutput:
        """Enroll a subject.

        Args:
            sample: The sample to generate the credential with. It can be a path to a file or a bytes object with the audio
                content
            applicant: The applicant to enroll
            content_type: The media type to declare for the sample, such as `audio/wav` or `image/jpeg`. Optional: it is inferred
                from the file extension for a path and from the magic bytes for a bytes object. Set it when the guess
                would be wrong, since VCSP answers with a 500 if the declared type does not match the content

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
        data_model = EnrollmentInput(sample=sample, applicant=applicant, content_type=content_type)
        endpoint = VcspEndpoints.ENROLLMENTS.value
        sample = self._get_sample(data_model.sample, data_model.content_type)
        files = {"sample": sample}
        data = {"applicant": json.dumps(data_model.applicant.model_dump(exclude_none=True))}
        response = self._post(
            endpoint=endpoint,
            files=files,
            data=data,
        )
        return EnrollmentOutput(**response.json())

    def _get_sample(self, sample: str | bytes, content_type: str | None = None) -> tuple[str, bytes, str]:
        """Return the filename, the content and the media type of a sample.

        Args:
            sample: A path to a file, or the content itself as bytes
            content_type: Media type to declare. When omitted it is taken from the file
                extension for a path, and from the magic bytes for a bytes object

        Returns:
            The filename, the content and the media type to send

        Raises:
            TypeError: If `sample` is neither a string nor a bytes object

        """
        if isinstance(sample, str):
            filename = os.path.basename(sample)
            with open(sample, "rb") as f:
                file = f.read()
            guessed = mimetypes.guess_type(sample)[0]
        elif isinstance(sample, bytes):
            filename = "sample"
            file = sample
            guessed = guess_content_type(sample)
        else:
            error = "sample must be a string or a bytes object"
            raise TypeError(error)
        return filename, file, content_type or guessed or DEFAULT_CONTENT_TYPE

    @legacy_model_argument(GetAccountInput)
    def get_account(
        self,
        subject_id: str,
    ) -> GetAccountOutput:
        """Get an account.

        Args:
            subject_id: The account_id to get

        Returns:
            GetAccountOutput: The output of the account

        Raises:
            AccountNotFoundError: If the account is not found

        """
        data_model = GetAccountInput(subject_id=subject_id)
        endpoint = VcspEndpoints.ACCOUNTS.value.replace("<subject_id>", data_model.subject_id)
        response = self._get(endpoint=endpoint)
        return GetAccountOutput(**response.json())

    @legacy_model_argument(DeleteAccountInput)
    def delete_account(
        self,
        subject_id: str,
    ) -> None:
        """Delete an account.

        Args:
            subject_id: The account_id to delete

        Raises:
            AccountNotFoundError: If the account is not found

        """
        data_model = DeleteAccountInput(subject_id=subject_id)
        endpoint = VcspEndpoints.ACCOUNTS.value.replace("<subject_id>", data_model.subject_id)
        self._delete(endpoint=endpoint)

    @legacy_model_argument(GetCredentialsInput)
    def get_all_subject_credentials(
        self,
        subject_id: str,
    ) -> GetCredentialsOutput:
        """Get all credentials for a subject.

        Args:
            subject_id: The account_id to get the credentials from

        Returns:
            GetCredentialsOutput: The output of the credentials

        Raises:
            AccountNotFoundError: If the account is not found

        """
        data_model = GetCredentialsInput(subject_id=subject_id)
        endpoint = VcspEndpoints.CREDENTIALS.value.replace("<subject_id>", data_model.subject_id)
        response = self._get(endpoint=endpoint)
        return GetCredentialsOutput(credentials=response.json())

    @legacy_model_argument(GetCredentialInput)
    def get_credential(
        self,
        credential_id: str,
        subject_id: str,
    ) -> GetCredentialOutput:
        """Get a credential.

        Args:
            credential_id: The credential_id to get
            subject_id: The subject_id to get the credential from

        Returns:
            GetCredentialOutput: The output of the credential

        Raises:
            CredentialNotFoundError: If the credential is not found
            AccountNotFoundError: If the account is not found

        """
        data_model = GetCredentialInput(credential_id=credential_id, subject_id=subject_id)
        endpoint = VcspEndpoints.CREDENTIAL_ID.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        response = self._get(endpoint=endpoint)
        return GetCredentialOutput(**response.json())

    @legacy_model_argument(DeleteCredentialInput)
    def delete_credential(
        self,
        credential_id: str,
        subject_id: str,
    ) -> None:
        """Delete a credential.

        Args:
            credential_id: The credential_id to delete
            subject_id: The subject from which the credential will be deleted

        """
        data_model = DeleteCredentialInput(credential_id=credential_id, subject_id=subject_id)
        endpoint = VcspEndpoints.CREDENTIAL_ID.value.replace("<subject_id>", data_model.subject_id)
        endpoint = endpoint.replace("<credential_id>", data_model.credential_id)
        self._delete(endpoint=endpoint)

    @legacy_model_argument(CreateTagsInput)
    def create_tags(
        self,
        tags: list[str],
    ) -> CreateTagsOutput:
        """Create tags.

        Args:
            tags: The tags to create

        Returns:
            CreateTagsOutput: The output of the tags creation

        Raises:
            TagsLimitExceededError: If the tag limit is exceeded
            TagAlreadyExistsError: If the tag already exists
            TagListEmptyError: If the tag list is empty

        """
        data_model = CreateTagsInput(tags=tags)
        endpoint = VcspEndpoints.TAGS.value
        response = self._post(endpoint=endpoint, json_=data_model.model_dump())
        return CreateTagsOutput(**response.json())

    def get_tags(self) -> GetTagsOutput:
        """Get every tag created in the system.

        Returns:
            GetTagsOutput: The tags, paginated

        """
        endpoint = VcspEndpoints.TAGS.value
        response = self._get(endpoint=endpoint)
        return GetTagsOutput(**response.json())

    @legacy_model_argument(DeleteTagInput)
    def delete_tag(
        self,
        name: str,
    ) -> None:
        """Delete a tag.

        Args:
            name: The name of the tag

        Raises:
            InvalidTagsError: If the tag is invalid

        """
        data_model = DeleteTagInput(name=name)
        endpoint = VcspEndpoints.TAGS_NAME.value.replace("<tag_name>", data_model.name)
        self._delete(endpoint=endpoint)

    @legacy_model_argument(CreateGroupInput)
    def create_group(
        self,
        name: str,
        credential_configuration_urn: str,
        description: str | None = None,
        expired_at: str | None = None,
    ) -> CreateGroupOutput:
        """Create a group.

        Args:
            name: The name of the group. Must match `^[a-zA-Z_][a-zA-Z0-9_]{2,63}$`, so letters, digits and underscores only,
                starting with a letter or an underscore
            credential_configuration_urn: The credential configuration the group holds
            description: A free-text description. Defaults to empty on the service
            expired_at: How long credentials are retained in the group, as an **ISO 8601 duration** such as `P1Y` or `P30D` — not
                a date. The service answers with the resulting timestamp. Defaults to five years

        Returns:
            CreateGroupOutput: The output of the group creation

        Raises:
            GroupsLimitExceededError: If the group limit is exceeded
            GroupAlreadyExistsError: If the group already exists
            InvalidCredentialConfigurationUrnError: If the credential configuration urn is invalid

        """
        data_model = CreateGroupInput(
            name=name, credential_configuration_urn=credential_configuration_urn, description=description, expired_at=expired_at
        )
        endpoint = VcspEndpoints.GROUPS.value
        response = self._post(endpoint=endpoint, json_=data_model.model_dump(exclude_none=True))
        return CreateGroupOutput(**response.json())

    @legacy_model_argument(GetGroupsInput)
    def get_groups(
        self,
        size: int | None = 100,
        page: int | None = 1,
    ) -> GetGroupsOutput:
        """Get all groups.

        Args:
            size: The size of the groups (optional), default is 100
            page: The page number (optional), default is 1

        Returns:
            GetGroupsOutput: The output of the groups

        """
        data_model = GetGroupsInput(size=size, page=page)
        endpoint = VcspEndpoints.GROUPS.value
        endpoint = endpoint + f"?size={data_model.size}&page={data_model.page}"
        response = self._get(endpoint=endpoint)
        items = response.json()["items"]
        total = response.json()["total"]
        page = response.json()["page"]
        size = response.json()["size"]
        pages = response.json()["pages"]
        return GetGroupsOutput(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages,
        )

    @legacy_model_argument(GetGroupInput)
    def get_group(
        self,
        name: str,
    ) -> GetGroupOutput:
        """Get a group.

        Args:
            name: The name of the group

        Returns:
            GetGroupOutput: The output of the group

        Raises:
            GroupNotFoundError: If the group is not found

        """
        data_model = GetGroupInput(name=name)
        endpoint = VcspEndpoints.GROUP_NAME.value.replace("<group_name>", data_model.name)
        response = self._get(endpoint=endpoint)
        return GetGroupOutput(**response.json())

    @legacy_model_argument(DeleteGroupInput)
    def delete_group(
        self,
        name: str,
    ) -> None:
        """Delete a group.

        Args:
            name: The name of the group

        Raises:
            GroupNotFoundError: If the group is not found

        """
        data_model = DeleteGroupInput(name=name)
        endpoint = VcspEndpoints.GROUP_NAME.value.replace("<group_name>", data_model.name)
        self._delete(endpoint=endpoint)

    @legacy_model_argument(GetGroupMembersInput)
    def get_group_members(
        self,
        name: str,
    ) -> GetGroupMembersOutput:
        """Get the members of a group.

        Args:
            name: The name of the group

        Returns:
            GetGroupMembersOutput: The output of the group members

        Raises:
            GroupNotFoundError: If the group is not found

        """
        data_model = GetGroupMembersInput(name=name)
        endpoint = VcspEndpoints.GROUP_MEMBERS.value.replace("<group_name>", data_model.name)
        response = self._get(endpoint=endpoint)
        return GetGroupMembersOutput(**response.json())
