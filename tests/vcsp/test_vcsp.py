import io
import tarfile
import uuid

import pytest
from pydantic import ValidationError

from tests.vcsp.conftest import SUBJECT_PREFIX, TEST_TAG, unique_group_name
from vericlient.vcsp.exceptions import (
    AccountNotFoundError,
    AssuranceMethodNotFoundError,
    AssuranceValidationError,
    ClusteringNotSupportedError,
    CredentialNotFoundError,
    EmptyFileError,
    FaceNotFoundError,
    FaceTooSmallError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
    InsufficientQualityError,
    InvalidAssuranceError,
    InvalidAssuranceMethodUrnError,
    InvalidAudioFormatError,
    InvalidBatchFileError,
    InvalidCredentialConfigurationUrnError,
    InvalidSnrError,
    InvalidTagsError,
    RequestValidationError,
    TagAlreadyExistsError,
    TagListEmptyError,
    TaskNotFoundError,
    UnsupportedMediaTypeError,
    VoiceDurationIsNotEnoughError,
)
from vericlient.vcsp.models import (
    Applicant,
    BatchApplicant,
    CredentialTagAction,
    GetAccountInput,
    GroupAction,
    GroupClaimant,
    GroupMembershipSource,
    SubjectClaimant,
)


def skip_if_not_mock(mock_server):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")


@pytest.mark.vcsp
def test_vcsp_alive(vcsp_client, mock_server, vcsp_alive_parameters):
    if mock_server:
        for param in vcsp_alive_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    response = vcsp_client.alive()
    assert response


@pytest.mark.vcsp
def test_get_credential_configurations(
    vcsp_client,
    mock_server,
    vcsp_credential_configurations_response,
    vcsp_credential_configuration_parameters,
):
    if mock_server:
        for param in vcsp_credential_configuration_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    response = vcsp_client.get_credential_configurations()

    assert isinstance(response.credential_configurations, list)

    if mock_server:
        assert response.credential_configurations == vcsp_credential_configurations_response


@pytest.mark.vcsp
def test_get_assurance_methods(
    vcsp_client,
    mock_server,
    vcsp_assurance_methods_response,
    vcsp_assurance_methods_parameters,
):
    if mock_server:
        for param in vcsp_assurance_methods_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    response = vcsp_client.get_assurance_methods()

    assert isinstance(response.assurance_methods, list)

    if mock_server:
        assert response.assurance_methods == vcsp_assurance_methods_response


@pytest.mark.vcsp
def test_get_assurance_method_info_success(
    vcsp_client,
    mock_server,
    vcsp_assurance_method_response,
    vcsp_assurance_method_info_parameters,
    valid_assurance_method_urn,
):

    if mock_server:
        for param in vcsp_assurance_method_info_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)
    else:
        valid_assurance_method_urn = vcsp_client.get_assurance_methods().assurance_methods[0]

    response = vcsp_client.get_assurance_method_info(
        urn=valid_assurance_method_urn,
    )

    assert response.urn == valid_assurance_method_urn
    assert hasattr(response.json_schema, "json_schema")
    assert hasattr(response.json_schema, "title")
    assert hasattr(response.json_schema, "type")
    assert hasattr(response.json_schema, "properties")

    if mock_server:
        assert response.json_schema.json_schema == vcsp_assurance_method_response["schema"]["$schema"]
        assert response.json_schema.title == vcsp_assurance_method_response["schema"]["title"]
        assert response.json_schema.type == vcsp_assurance_method_response["schema"]["type"]
        assert response.json_schema.properties == vcsp_assurance_method_response["schema"]["properties"]


@pytest.mark.vcsp
def test_get_assurance_method_info_not_found(
    vcsp_client,
    mock_server,
    vcsp_assurance_method_not_found_parameters,
):
    invalid_urn = "urn:vcsp:assurance_methods:invalid:method:v1"

    if mock_server:
        for param in vcsp_assurance_method_not_found_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    with pytest.raises(AssuranceMethodNotFoundError):
        vcsp_client.get_assurance_method_info(
            urn=invalid_urn,
        )


@pytest.mark.vcsp
def test_mock_vcsp_enroll_subject(vcsp_client, mock_server, vcsp_enrollment_parameters, audio_file_path, test_subject_id):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for param in vcsp_enrollment_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.enroll_subject(
            sample=audio_file_path,
            applicant=Applicant(
                credential_configuration_urn="fake-credential_configuration_urn",
                assurance_method_urn="fake-assurance_method_urn",
                assurance={},
            ),
        )

        assert response.credential_id == "fake-credential_id"
        assert response.subject_id == test_subject_id


@pytest.mark.vcsp
def test_vcsp_enrollment_exception(vcsp_client, mock_server, vcsp_enrollment_exception_parameters, audio_file_path):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_enrollment_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.enroll_subject(
                    sample=audio_file_path,
                    applicant=Applicant(
                        credential_configuration_urn="fake-credential_configuration_urn",
                        assurance_method_urn="fake-assurance_method_urn",
                        assurance={},
                    ),
                )


@pytest.mark.vcsp
def test_get_account(vcsp_client, mock_server, vcsp_get_account_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_account(subject_id=test_subject_id)
        assert response.subject_id == test_subject_id


@pytest.mark.vcsp
def test_delete_account(vcsp_client, mock_server, vcsp_delete_account_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_account(subject_id=test_subject_id)
        assert response is None


@pytest.mark.vcsp
def test_get_all_credentials(vcsp_client, mock_server, vcsp_get_all_credentials_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_all_credentials_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_all_subject_credentials(subject_id=test_subject_id)
        for cred_response, cred_mock in zip(response.credentials, mock_response, strict=False):
            assert cred_response.id == cred_mock["id"]
            assert cred_response.sample.type == cred_mock["sample"]["type"]
            assert cred_response.sample.valid_from == cred_mock["sample"]["valid_from"]
            assert cred_response.sample.valid_until == cred_mock["sample"]["valid_until"]
            assert cred_response.sample.content_type == cred_mock["sample"]["content_type"]
            assert cred_response.sample.analysis == cred_mock["sample"]["analysis"]
            assert cred_response.groups == cred_mock["groups"]
            assert cred_response.issuer == cred_mock["issuer"]


@pytest.mark.vcsp
def test_get_credential(vcsp_client, mock_server, vcsp_get_credential_parameters, test_subject_id, test_credential_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_credential_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_credential(
            subject_id=test_subject_id,
            credential_id=test_credential_id,
        )
        assert response.id == mock_response["id"]
        assert response.sample.type == mock_response["sample"]["type"]
        assert response.sample.valid_from == mock_response["sample"]["valid_from"]
        assert response.sample.valid_until == mock_response["sample"]["valid_until"]
        assert response.sample.content_type == mock_response["sample"]["content_type"]
        assert response.sample.analysis == mock_response["sample"]["analysis"]
        assert response.groups == mock_response["groups"]
        assert response.issuer == mock_response["issuer"]


@pytest.mark.vcsp
def test_delete_credential(vcsp_client, mock_server, vcsp_delete_credential_parameters, test_subject_id, test_credential_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_credential_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_credential(
            subject_id=test_subject_id,
            credential_id=test_credential_id,
        )
        assert response is None


@pytest.mark.vcsp
def test_create_tags(vcsp_client, mock_server, vcsp_create_tags_parameters, test_tag_name, test_tag_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_create_tags_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.create_tags(tags=[test_tag_name, test_tag_name_2])
        assert response.tags == [test_tag_name, test_tag_name_2]
        assert response.created_at == mock_response["created_at"]


@pytest.mark.vcsp
def test_vcsp_create_tags_exception(
    vcsp_client,
    mock_server,
    vcsp_create_tags_exception_parameters,
    test_tag_name,
    test_tag_name_2,
):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_create_tags_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.create_tags(tags=[test_tag_name, test_tag_name_2])


@pytest.mark.vcsp
def test_get_tags(vcsp_client, mock_server, vcsp_get_tags_parameters, test_tag_name, test_tag_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_tags_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_tags()
        assert response.items[0].name == test_tag_name
        assert response.items[1].name == test_tag_name_2
        assert response.total == 2
        assert response.page == 1
        assert response.size == 100
        assert response.pages == 1


@pytest.mark.vcsp
def test_delete_tag(vcsp_client, mock_server, vcsp_delete_tag_parameters, test_tag_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_tag_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_tag(name=test_tag_name)
        assert response is None


@pytest.mark.vcsp
def test_vcsp_delete_tag_exception(vcsp_client, mock_server, vcsp_delete_tag_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_delete_tag_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.delete_tag(name="invalid_tag")


@pytest.mark.vcsp
def test_create_group(vcsp_client, mock_server, vcsp_create_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_create_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.create_group(
            name=test_group_name,
            credential_configuration_urn="urn:vcsp:credential_configurations:face:selfie:v1",
            description="test:group",
            expired_at="P1Y",
        )
        assert response.name == test_group_name
        assert response.credential_configuration_urn == mock_response["credential_configuration_urn"]
        assert response.size == mock_response["size"]
        assert response.description == mock_response["description"]
        assert response.expired_at == mock_response["expired_at"]
        assert response.created_at == mock_response["created_at"]
        assert response.updated_at == mock_response["updated_at"]


@pytest.mark.vcsp
def test_vcsp_create_group_exception(
    vcsp_client,
    mock_server,
    vcsp_create_group_exception_parameters,
    test_group_name,
):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_create_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.create_group(
                    name=test_group_name,
                    credential_configuration_urn="urn:vcsp:credential_configurations:face:selfie:v1",
                    description="test:group",
                    expired_at="P1Y",
                )


@pytest.mark.vcsp
def test_get_groups(vcsp_client, mock_server, vcsp_get_groups_parameters, test_group_name, test_group_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_groups_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        # `name` used to be passed here and silently dropped: GetGroupsInput never had it,
        # and this endpoint lists every group rather than looking one up.
        response = vcsp_client.get_groups()
        assert response.items[0].name == test_group_name
        assert response.items[1].name == test_group_name_2
        assert response.total == 2
        assert response.page == 1
        assert response.size == 100
        assert response.pages == 1


@pytest.mark.vcsp
def test_vcsp_get_group_exception(vcsp_client, mock_server, vcsp_get_group_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_get_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.get_group(name="nonexistent_group_name")


@pytest.mark.vcsp
def test_get_group(vcsp_client, mock_server, vcsp_get_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_group(name=test_group_name)
        assert response.name == test_group_name
        assert response.credential_configuration_urn == mock_response["credential_configuration_urn"]
        assert response.size == mock_response["size"]
        assert response.description == mock_response["description"]
        assert response.expired_at == mock_response["expired_at"]
        assert response.created_at == mock_response["created_at"]
        assert response.updated_at == mock_response["updated_at"]


@pytest.mark.vcsp
def test_delete_group(vcsp_client, mock_server, vcsp_delete_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_group(name=test_group_name)
        assert response is None


@pytest.mark.vcsp
def test_vcsp_delete_group_exception(vcsp_client, mock_server, vcsp_delete_group_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_delete_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.delete_group(name="nonexistent_group_name")


@pytest.mark.vcsp
def test_get_group_members(vcsp_client, mock_server, vcsp_get_group_members_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_group_members_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_group_members(name=test_group_name)
        assert response.items[0].subject_id == mock_response["items"][0]["subject_id"]
        assert response.items[0].credential_id == mock_response["items"][0]["credential_id"]
        assert response.items[0].expired_in_group == mock_response["items"][0]["expired_in_group"]
        assert response.items[0].claims == mock_response["items"][0]["claims"]
        assert response.items[0].tags == mock_response["items"][0]["tags"]
        assert response.total == 2
        assert response.page == 1
        assert response.size == 100
        assert response.pages == 1


@pytest.mark.vcsp
def test_vcsp_get_group_members_exception(vcsp_client, mock_server, vcsp_get_group_members_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_get_group_members_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.get_group_members(name="nonexistent_group_name")


# ---------------------------------------------------------------------------
# Real-infrastructure lifecycle tests
#
# These run only against a sandbox and create genuine resources. Every fixture they use
# removes what it created, and the session sweeper picks up anything a crashed run left
# behind. See the conftest for the naming rules and the guard rails.
# ---------------------------------------------------------------------------


@pytest.mark.vcsp
def test_real_tag_lifecycle(real_writes, temp_tag):
    """A created tag shows up in the listing, and disappears once the fixture tears down."""
    names = [tag.name for tag in real_writes.get_tags().items]
    assert temp_tag in names


@pytest.mark.vcsp
def test_real_tag_is_gone_after_teardown(real_writes, resource_tracker):
    """Deleting a tag really removes it, rather than the listing being stale."""
    real_writes.create_tags(tags=[TEST_TAG])
    resource_tracker.add("tag", TEST_TAG, lambda: real_writes.delete_tag(name=TEST_TAG))

    assert TEST_TAG in [tag.name for tag in real_writes.get_tags().items]

    real_writes.delete_tag(name=TEST_TAG)
    resource_tracker.forget(TEST_TAG)

    assert TEST_TAG not in [tag.name for tag in real_writes.get_tags().items]


@pytest.mark.vcsp
def test_real_group_lifecycle(real_writes, temp_group, voice_credential_configuration):
    """A created group can be read back, is listed, and starts empty."""
    group = real_writes.get_group(name=temp_group)
    assert group.name == temp_group
    assert group.credential_configuration_urn == voice_credential_configuration
    assert group.size == 0

    assert temp_group in [g.name for g in real_writes.get_groups().items]

    members = real_writes.get_group_members(name=temp_group)
    assert members.total == 0
    assert members.items == []


@pytest.mark.vcsp
def test_real_group_defaults(real_writes, resource_tracker, voice_credential_configuration):
    """`description` and `expired_at` are optional, and the service fills them in.

    `expired_at` goes out as an ISO 8601 duration and comes back as a timestamp, which is
    worth pinning down because the asymmetry is easy to get wrong.
    """
    name = unique_group_name()
    created = real_writes.create_group(
        name=name,
        credential_configuration_urn=voice_credential_configuration,
    )
    resource_tracker.add("group", name, lambda: real_writes.delete_group(name=name))

    assert created.description == ""
    assert created.expired_at.startswith("20")


@pytest.mark.vcsp
def test_real_subject_lifecycle(real_writes, temp_subject):
    """Enrol a subject, read the account and its credentials back, then let teardown remove it."""
    subject_id, credential_id = temp_subject

    account = real_writes.get_account(subject_id=subject_id)
    assert account.subject_id == subject_id
    assert credential_id in account.credentials

    credentials = real_writes.get_all_subject_credentials(
        subject_id=subject_id,
    ).credentials
    assert [c.id for c in credentials] == [credential_id]

    credential = real_writes.get_credential(
        subject_id=subject_id,
        credential_id=credential_id,
    )
    assert credential.id == credential_id
    assert credential.sample.type == "voice"


@pytest.mark.vcsp
def test_real_deleted_account_is_gone(real_writes, temp_subject, resource_tracker):
    """Deleting an account removes it and its credentials, not just the account row."""
    subject_id, _ = temp_subject

    real_writes.delete_account(subject_id=subject_id)
    resource_tracker.forget(subject_id)

    with pytest.raises(AccountNotFoundError):
        real_writes.get_account(subject_id=subject_id)


@pytest.mark.vcsp
def test_real_list_credentials_by_tag(real_writes, temp_subject, shared_test_tag):
    """The system-wide listing finds a credential by its tag, and reports its account.

    This is the query the session sweeper depends on: the deployment holds six figures of
    credentials, so filtering by tag is the only way to find the ones a run created.
    """
    subject_id, credential_id = temp_subject

    listed = real_writes.list_credentials(tags=[shared_test_tag])

    matching = [c for c in listed.items if c.id == credential_id]
    assert matching, f"credential {credential_id} not found among {listed.total} tagged credentials"
    assert matching[0].subject_id == subject_id
    assert shared_test_tag in matching[0].tags


@pytest.mark.vcsp
def test_real_list_credentials_pages(real_writes):
    """Paging is honoured, which matters because the listing is unbounded by default."""
    page = real_writes.list_credentials(size=2, page=1)
    assert len(page.items) <= 2
    assert page.page == 1
    assert page.size == 2
    assert page.total >= len(page.items)


@pytest.mark.vcsp
def test_real_credential_sample_round_trips(real_writes, temp_subject, audio_file):
    """The sample comes back byte for byte, with the media type it was sent as."""
    subject_id, credential_id = temp_subject

    sample = real_writes.get_credential_sample(
        subject_id=subject_id,
        credential_id=credential_id,
    )

    assert sample.content == audio_file
    assert sample.content_type.startswith("audio/")


@pytest.mark.vcsp
def test_real_credential_configuration_has_a_claims_schema(real_writes, voice_credential_configuration):
    """One configuration can be read on its own, with the schema its claims must satisfy."""
    configuration = real_writes.get_credential_configuration(
        urn=voice_credential_configuration,
    )

    assert configuration.urn == voice_credential_configuration
    assert isinstance(configuration.claims_schema, dict)


@pytest.mark.vcsp
def test_real_delete_credentials_of_an_empty_group(real_writes, temp_group):
    """Bulk deletion accepts a group with nothing in it.

    Group membership is not implemented yet, so this pins down the request shape rather than
    the deletion. The specification is wrong about it twice: it documents a multipart body
    wrapping the filters, and the service wants a flat JSON one.
    """
    real_writes.delete_credentials(
        group_name=temp_group,
        delete_empty_accounts=True,
    )

    assert real_writes.get_group(name=temp_group).size == 0


@pytest.mark.vcsp
def test_real_task_listing_is_paginated(real_writes):
    """The task listing answers even with nothing running."""
    tasks = real_writes.get_tasks()
    assert tasks.page == 1
    assert tasks.total >= 0
    assert len(tasks.items) <= tasks.size


@pytest.mark.vcsp
def test_real_unknown_task_is_reported(real_writes):
    """A task id that does not exist raises rather than returning an empty task."""
    unknown = "00000000-0000-0000-0000-000000000000"

    with pytest.raises(TaskNotFoundError):
        real_writes.get_task(task_id=unknown)

    with pytest.raises(TaskNotFoundError):
        real_writes.delete_task(task_id=unknown)


@pytest.mark.vcsp
def test_real_batch_enrollment_runs_as_a_task(
    real_writes,
    resource_tracker,
    shared_test_tag,
    audio_file,
    voice_credential_configuration,
    enrollment_assurance_method,
):
    """Enrol two applicants at once, follow the task, and read the outcome.

    This is the full asynchronous path: the archive the client builds, the 202 with a task
    handle, the polling, and the per-applicant report.
    """
    subject_ids = [f"{SUBJECT_PREFIX}-{uuid.uuid4()}" for _ in range(2)]
    for subject_id in subject_ids:
        resource_tracker.add(
            "account",
            subject_id,
            lambda subject_id=subject_id: real_writes.delete_account(
                subject_id=subject_id,
            ),
        )

    batch = real_writes.enroll_batch(
        applicants=[
            BatchApplicant(
                sample=audio_file,
                filename=f"sample_{index}.wav",
                applicant=Applicant(
                    subject_id=subject_id,
                    credential_configuration_urn=voice_credential_configuration,
                    assurance_method_urn=enrollment_assurance_method,
                    assurance={"authenticity_threshold": 0.5},
                    tags=[shared_test_tag],
                ),
            )
            for index, subject_id in enumerate(subject_ids)
        ],
    )
    resource_tracker.add(
        "task",
        batch.task_id,
        lambda: real_writes.delete_task(task_id=batch.task_id),
    )

    task = real_writes.wait_for_task(task_id=batch.task_id, timeout=120)
    assert task.succeeded, f"batch task finished as {task.status}"
    assert task.is_finished
    assert task.progress == 100
    assert task.finished_at

    result = real_writes.get_task_result(task_id=batch.task_id).result
    assert result["summary"] == {"total": 2, "success": 2, "error": 0}
    assert sorted(item["subject_id"] for item in result["report"]) == sorted(subject_ids)
    assert {item["status"] for item in result["report"]} == {"success"}

    # The accounts really exist, rather than the report just saying so.
    for subject_id in subject_ids:
        assert real_writes.get_account(subject_id=subject_id).credentials


@pytest.mark.vcsp
def test_real_batch_rejects_a_tar_without_applicants(real_writes):
    """A TAR missing applicants.json is refused, rather than silently enrolling nothing."""
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w") as tar:
        info = tarfile.TarInfo(name="sample.wav")
        info.size = 4
        tar.addfile(info, io.BytesIO(b"fake"))

    with pytest.raises(InvalidBatchFileError):
        real_writes.enroll_batch(batch_file=archive.getvalue())


@pytest.mark.vcsp
def test_real_batch_rejects_something_that_is_not_an_archive(real_writes):
    """Bytes that are not a TAR at all come back as an unsupported media type, not a bad batch.

    Worth pinning: the service distinguishes "this is not an archive" from "this archive is
    wrong", and they surface as different exceptions.
    """
    with pytest.raises(UnsupportedMediaTypeError):
        real_writes.enroll_batch(batch_file=b"not a tar archive")


@pytest.mark.vcsp
def test_real_populate_a_group_and_match_against_it(
    real_writes,
    temp_group,
    temp_subject,
    audio_file,
    matching_assurance_method,
):
    """The whole 1:N path: put a credential in a group, then match a sample against it.

    This is what groups are for, so it is worth exercising as one flow rather than as two
    endpoints that each returned a 200.
    """
    subject_id, credential_id = temp_subject

    group = real_writes.modify_group(
        name=temp_group,
        action=GroupAction.POPULATE,
        from_=GroupMembershipSource(subjects=[subject_id]),
    )
    assert group.size == 1

    members = real_writes.get_group_members(name=temp_group)
    assert [member.credential_id for member in members.items] == [credential_id]
    assert members.items[0].subject_id == subject_id

    matched = real_writes.match(
        sample=audio_file,
        claimant=GroupClaimant(
            group_name=temp_group,
            assurance_method_urn=matching_assurance_method,
            assurance={"biometric_threshold": 0.5},
            limit=5,
        ),
    )
    assert matched.nhits == 1
    assert matched.results[0].subject_id == subject_id
    assert matched.results[0].match_status == "HIT"
    assert matched.sample.type == "voice"

    # And removing it empties the group again.
    emptied = real_writes.modify_group(
        name=temp_group,
        action=GroupAction.REMOVE,
        from_=GroupMembershipSource(subjects=[subject_id]),
    )
    assert emptied.size == 0


@pytest.mark.vcsp
def test_real_one_to_one_matching(
    real_writes,
    temp_subject,
    audio_file,
    voice_credential_configuration,
    matching_assurance_method,
):
    """Matching a sample against the subject it was enrolled with is a hit."""
    subject_id, _ = temp_subject

    matched = real_writes.match(
        sample=audio_file,
        claimant=SubjectClaimant(
            subject_id=subject_id,
            credential_configuration_urn=voice_credential_configuration,
            assurance_method_urn=matching_assurance_method,
            assurance={"biometric_threshold": 0.5},
        ),
    )

    assert matched.nhits == 1
    assert matched.results[0].subject_id == subject_id
    assert matched.results[0].biometrics_score > 0.5
    assert matched.sample.analysis["net_speech_duration"] > 3


@pytest.mark.vcsp
def test_real_credential_tags_can_be_added_and_removed(real_writes, temp_subject, shared_test_tag):
    """Tags move on and off a credential, and the credential comes back each time."""
    subject_id, credential_id = temp_subject
    target = {
        "subject_id": subject_id,
        "credential_id": credential_id,
        "tags": [shared_test_tag],
    }

    without = real_writes.modify_credential_tags(action=CredentialTagAction.REMOVE, **target)
    assert shared_test_tag not in without.tags

    restored = real_writes.modify_credential_tags(action=CredentialTagAction.ADD, **target)
    assert shared_test_tag in restored.tags
    assert restored.id == credential_id


@pytest.mark.vcsp
def test_real_clustering_is_refused_for_a_voice_group(
    real_writes,
    temp_group,
    clustering_assurance_method,
):
    """Clustering only runs on face credentials, and says so rather than failing obscurely.

    A face group would need a face fixture, which this repository does not have yet, so this
    pins the rejection instead.
    """
    with pytest.raises(ClusteringNotSupportedError):
        real_writes.start_clustering(
            name=temp_group,
            assurance_method_urn=clustering_assurance_method,
            properties={"similarity_threshold": 0.5, "mode": "similarity_based"},
        )


@pytest.mark.vcsp
def test_real_deleting_a_credential_leaves_the_account(real_writes, temp_subject):
    """Deleting one credential removes it without taking the account with it.

    The distinction matters: `delete_account` removes everything, this does not, and the
    mocked test could not tell the difference because it never looked at the account after.
    """
    subject_id, credential_id = temp_subject

    real_writes.delete_credential(
        subject_id=subject_id,
        credential_id=credential_id,
    )

    account = real_writes.get_account(subject_id=subject_id)
    assert credential_id not in account.credentials

    with pytest.raises(CredentialNotFoundError):
        real_writes.get_credential(
            subject_id=subject_id,
            credential_id=credential_id,
        )


# ---------------------------------------------------------------------------
# Error paths, provoked against the real service rather than mocked.
#
# A mocked error body only proves the client maps a code it was handed. These send input the
# service genuinely rejects. None of them can succeed, so none of them leaves anything behind
# — which is why they need no resource tracking.
# ---------------------------------------------------------------------------


def _applicant(configuration: str, assurance_method: str, **overrides: object) -> Applicant:
    """Build an applicant for an enrolment that is meant to fail."""
    fields = {
        "subject_id": f"{SUBJECT_PREFIX}-rejected-{uuid.uuid4().hex[:8]}",
        "credential_configuration_urn": configuration,
        "assurance_method_urn": assurance_method,
        "assurance": {"authenticity_threshold": 0.5},
    }
    fields.update(overrides)
    return Applicant(**fields)


@pytest.mark.vcsp
@pytest.mark.parametrize(
    ("sample_fixture", "expected"),
    [
        ("audio_not_enough_speech_file_path", VoiceDurationIsNotEnoughError),
        ("audio_bad_snr_file_path", InvalidSnrError),
        ("audio_insufficient_quality_file_path", InsufficientQualityError),
        ("audio_too_many_channels_file_path", InvalidAudioFormatError),
        ("audio_invalid_sample_rate_file_path", InvalidAudioFormatError),
        ("empty_file_path", EmptyFileError),
    ],
)
def test_real_voice_enrollment_rejects_bad_audio(
    real_writes,
    request,
    voice_credential_configuration,
    enrollment_assurance_method,
    sample_fixture,
    expected,
):
    """Each way an audio sample can be unusable maps to its own exception.

    Worth separating: a caller can retry a short recording, and cannot do anything about a
    file that arrived empty.
    """
    with pytest.raises(expected):
        real_writes.enroll_subject(
            sample=request.getfixturevalue(sample_fixture),
            applicant=_applicant(voice_credential_configuration, enrollment_assurance_method),
        )


@pytest.mark.vcsp
def test_real_voice_enrollment_rejects_a_sample_that_is_not_audio(
    real_writes,
    voice_credential_configuration,
    enrollment_assurance_method,
    face_image_path,
):
    """A photo sent where a recording belongs is caught on its media type, before analysis."""
    with pytest.raises(UnsupportedMediaTypeError):
        real_writes.enroll_subject(
            sample=face_image_path,
            applicant=_applicant(voice_credential_configuration, enrollment_assurance_method),
        )


@pytest.mark.vcsp
@pytest.mark.parametrize(
    ("image_fixture", "expected"),
    [
        ("no_face_image_path", FaceNotFoundError),
        ("other_face_image_path", FaceTooSmallError),
        ("two_people_image_path", AssuranceValidationError),
    ],
)
def test_real_face_enrollment_rejects_bad_photos(
    real_writes,
    request,
    face_credential_configuration,
    enrollment_assurance_method,
    image_fixture,
    expected,
):
    """The face pipeline judges a photo on three separate grounds.

    Note the third: VCSP refuses a photo holding two people, where das-Face accepts the same
    image and quietly picks one of them (#30). The two services do not agree.
    """
    with pytest.raises(expected):
        real_writes.enroll_subject(
            sample=request.getfixturevalue(image_fixture),
            applicant=_applicant(face_credential_configuration, enrollment_assurance_method),
        )


@pytest.mark.vcsp
def test_real_enrollment_rejects_an_unknown_credential_configuration(
    real_writes,
    enrollment_assurance_method,
    audio_file_path,
):
    with pytest.raises(InvalidCredentialConfigurationUrnError):
        real_writes.enroll_subject(
            sample=audio_file_path,
            applicant=_applicant("urn:vcsp:credential_configurations:not_a_real_one:v1", enrollment_assurance_method),
        )


@pytest.mark.vcsp
def test_real_enrollment_rejects_an_unknown_assurance_method(
    real_writes,
    voice_credential_configuration,
    audio_file_path,
):
    with pytest.raises(InvalidAssuranceMethodUrnError):
        real_writes.enroll_subject(
            sample=audio_file_path,
            applicant=_applicant(voice_credential_configuration, "urn:vcsp:assurance_methods:not_a_real_one:v1"),
        )


@pytest.mark.vcsp
@pytest.mark.parametrize("assurance", [{}, {"authenticity_threshold": 5.0}], ids=["empty", "out of range"])
def test_real_enrollment_rejects_an_assurance_that_does_not_fit_the_method(
    real_writes,
    voice_credential_configuration,
    enrollment_assurance_method,
    audio_file_path,
    assurance,
):
    """The assurance is validated against the method's own schema, both ways it can miss."""
    with pytest.raises(InvalidAssuranceError):
        real_writes.enroll_subject(
            sample=audio_file_path,
            applicant=_applicant(
                voice_credential_configuration,
                enrollment_assurance_method,
                assurance=assurance,
            ),
        )


@pytest.mark.vcsp
def test_real_enrollment_rejects_a_tag_that_does_not_exist(
    real_writes,
    voice_credential_configuration,
    enrollment_assurance_method,
    audio_file_path,
):
    """A credential can only carry tags the subscription already knows about."""
    with pytest.raises(InvalidTagsError):
        real_writes.enroll_subject(
            sample=audio_file_path,
            applicant=_applicant(
                voice_credential_configuration,
                enrollment_assurance_method,
                tags=["vericlient:nosuchtag"],
            ),
        )


@pytest.mark.vcsp
def test_real_enrollment_rejects_a_tag_that_is_not_shaped_like_a_tag(
    real_writes,
    voice_credential_configuration,
    enrollment_assurance_method,
    audio_file_path,
):
    """A tag is `prefix:value`, and anything else fails validation before it is looked up.

    Different from the test above, and easy to confuse: this one never reaches the tag store.
    """
    with pytest.raises(RequestValidationError):
        real_writes.enroll_subject(
            sample=audio_file_path,
            applicant=_applicant(
                voice_credential_configuration,
                enrollment_assurance_method,
                tags=["no-colon-here"],
            ),
        )


@pytest.mark.vcsp
def test_real_reading_a_group_that_does_not_exist(real_vcsp):
    with pytest.raises(GroupNotFoundError):
        real_vcsp.get_group(name="vericlient_test_no_such_group")


@pytest.mark.vcsp
def test_real_creating_a_group_twice(real_writes, temp_group, voice_credential_configuration):
    """The second attempt is refused rather than silently reusing the first."""
    with pytest.raises(GroupAlreadyExistsError):
        real_writes.create_group(
            name=temp_group,
            credential_configuration_urn=voice_credential_configuration,
        )


@pytest.mark.vcsp
def test_real_creating_a_tag_twice(real_writes, own_tag):
    """Uses a tag of its own: `vericlient:test` is already held by a session fixture."""
    with pytest.raises(TagAlreadyExistsError):
        real_writes.create_tags(tags=[own_tag])


@pytest.mark.vcsp
def test_real_creating_no_tags_at_all(real_writes):
    """An empty list is refused rather than treated as a no-op."""
    with pytest.raises(TagListEmptyError):
        real_writes.create_tags(tags=[])


@pytest.mark.vcsp
def test_the_old_call_style_still_works_and_warns(vcsp_client, mock_server, vcsp_get_account_parameters, test_subject_id):
    """Passing the input model is deprecated, not broken, until 1.0.0."""
    skip_if_not_mock(mock_server)

    endpoint, mock_response, mock_status_code, *_ = vcsp_get_account_parameters[0]
    mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    with pytest.warns(DeprecationWarning, match="GetAccountInput"):
        vcsp_client.get_account(GetAccountInput(subject_id=test_subject_id))


@pytest.mark.vcsp
def test_vcsp_input_errors_name_the_method(vcsp_client):
    """The caller wrote `enroll_subject(...)`, so that is what the error says."""
    with pytest.raises(ValidationError) as raised:
        vcsp_client.enroll_subject(
            sample=123,
            applicant=Applicant(
                credential_configuration_urn="a-urn",
                assurance_method_urn="a-method",
                assurance={},
            ),
        )

    assert "enroll_subject()" in str(raised.value)
    assert "EnrollmentInput" not in str(raised.value)
    assert "expected a path to a file, or its content as bytes" in str(raised.value)
