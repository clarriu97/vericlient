
import pytest
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)
from vericlient.vcsp.models import (
    Applicant,
    AssuranceMethodInput,
    CreateGroupInput,
    CreateTagsInput,
    DeleteAccountInput,
    DeleteCredentialInput,
    DeleteGroupInput,
    DeleteTagInput,
    EnrollmentInput,
    GetAccountInput,
    GetCredentialInput,
    GetCredentialsInput,
    GetGroupInput,
    GetGroupMembersInput,
    GetGroupsInput,
)


def skip_if_not_mock(mock_server):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")


@pytest.mark.vcsp()
def test_vcsp_alive(vcsp_client, mock_server, vcsp_alive_parameters):
    if mock_server:
        for param in vcsp_alive_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    response = vcsp_client.alive()
    assert response


@pytest.mark.vcsp()
def test_get_credential_configurations(
        vcsp_client, mock_server,
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


@pytest.mark.vcsp()
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


@pytest.mark.vcsp()
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
        data_model=AssuranceMethodInput(urn=valid_assurance_method_urn),
    )

    assert response.urn == valid_assurance_method_urn
    assert hasattr(response.schema, "schema")
    assert hasattr(response.schema, "title")
    assert hasattr(response.schema, "type")
    assert hasattr(response.schema, "properties")

    if mock_server:
        assert response.schema.schema == vcsp_assurance_method_response["schema"]["$schema"]
        assert response.schema.title == vcsp_assurance_method_response["schema"]["title"]
        assert response.schema.type == vcsp_assurance_method_response["schema"]["type"]
        assert response.schema.properties == vcsp_assurance_method_response["schema"]["properties"]


@pytest.mark.vcsp()
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
            data_model=AssuranceMethodInput(urn=invalid_urn),
        )


@pytest.mark.vcsp()
def test_mock_vcsp_enroll_subject(vcsp_client, mock_server, vcsp_enrollment_parameters, audio_file_path, test_subject_id):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for param in vcsp_enrollment_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        input_model = EnrollmentInput(
            sample=audio_file_path,
            applicant=Applicant(
                credential_configuration_urn="fake-credential_configuration_urn",
                assurance_method_urn="fake-assurance_method_urn",
                assurance={},
            ),
        )

        response = vcsp_client.enroll_subject(data_model=input_model)

        assert response.credential_id == "fake-credential_id"
        assert response.subject_id == test_subject_id


@pytest.mark.vcsp()
def test_vcsp_enrollment_exception(vcsp_client, mock_server, vcsp_enrollment_exception_parameters, audio_file_path):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_enrollment_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            input_model = EnrollmentInput(
                sample=audio_file_path,
                applicant=Applicant(
                    credential_configuration_urn="fake-credential_configuration_urn",
                    assurance_method_urn="fake-assurance_method_urn",
                    assurance={},
                ),
            )
            with pytest.raises(exception):
                vcsp_client.enroll_subject(data_model=input_model)


@pytest.mark.vcsp()
def test_get_account(vcsp_client, mock_server, vcsp_get_account_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_account(data_model=GetAccountInput(subject_id=test_subject_id))
        assert response.subject_id == test_subject_id


@pytest.mark.vcsp()
def test_delete_account(vcsp_client, mock_server, vcsp_delete_account_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_account(data_model=DeleteAccountInput(subject_id=test_subject_id))
        assert response is None


@pytest.mark.vcsp()
def test_get_all_credentials(vcsp_client, mock_server, vcsp_get_all_credentials_parameters, test_subject_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_all_credentials_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_all_subject_credentials(data_model=GetCredentialsInput(subject_id=test_subject_id))
        for cred_response, cred_mock in zip(response.credentials, mock_response, strict=False):
            assert cred_response.id == cred_mock["id"]
            assert cred_response.sample.type == cred_mock["sample"]["type"]
            assert cred_response.sample.valid_from == cred_mock["sample"]["valid_from"]
            assert cred_response.sample.valid_until == cred_mock["sample"]["valid_until"]
            assert cred_response.sample.content_type == cred_mock["sample"]["content_type"]
            assert cred_response.sample.analysis == cred_mock["sample"]["analysis"]
            assert cred_response.groups == cred_mock["groups"]
            assert cred_response.issuer == cred_mock["issuer"]


@pytest.mark.vcsp()
def test_get_credential(vcsp_client, mock_server, vcsp_get_credential_parameters, test_subject_id, test_credential_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_credential_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_credential(
            data_model=GetCredentialInput(subject_id=test_subject_id, credential_id=test_credential_id),
        )
        assert response.id == mock_response["id"]
        assert response.sample.type == mock_response["sample"]["type"]
        assert response.sample.valid_from == mock_response["sample"]["valid_from"]
        assert response.sample.valid_until == mock_response["sample"]["valid_until"]
        assert response.sample.content_type == mock_response["sample"]["content_type"]
        assert response.sample.analysis == mock_response["sample"]["analysis"]
        assert response.groups == mock_response["groups"]
        assert response.issuer == mock_response["issuer"]


@pytest.mark.vcsp()
def test_delete_credential(vcsp_client, mock_server, vcsp_delete_credential_parameters, test_subject_id, test_credential_id):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_credential_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_credential(
            data_model=DeleteCredentialInput(
                subject_id=test_subject_id,
                credential_id=test_credential_id,
            ),
        )
        assert response is None


@pytest.mark.vcsp()
def test_create_tags(vcsp_client, mock_server, vcsp_create_tags_parameters, test_tag_name, test_tag_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_create_tags_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.create_tags(data_model=CreateTagsInput(tags=[test_tag_name, test_tag_name_2]))
        assert response.tags == [test_tag_name, test_tag_name_2]
        assert response.created_at == mock_response["created_at"]


@pytest.mark.vcsp()
def test_vcsp_create_tags_exception(
    vcsp_client, mock_server, vcsp_create_tags_exception_parameters,
    test_tag_name, test_tag_name_2,
):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_create_tags_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            input_model = CreateTagsInput(tags=[test_tag_name, test_tag_name_2])
            with pytest.raises(exception):
                vcsp_client.create_tags(data_model=input_model)


@pytest.mark.vcsp()
def test_get_tags(vcsp_client, mock_server, vcsp_get_tags_parameters, test_tag_name, test_tag_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_tags_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_tags()
        assert response.items[0].name == test_tag_name
        assert response.items[1].name == test_tag_name_2
        assert response.total == 2   # noqa: PLR2004
        assert response.page == 1
        assert response.size == 100  # noqa: PLR2004
        assert response.pages == 1


@pytest.mark.vcsp()
def test_delete_tag(vcsp_client, mock_server, vcsp_delete_tag_parameters, test_tag_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_tag_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_tag(data_model=DeleteTagInput(name=test_tag_name))
        assert response is None


@pytest.mark.vcsp()
def test_vcsp_delete_tag_exception(vcsp_client, mock_server, vcsp_delete_tag_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_delete_tag_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.delete_tag(data_model=DeleteTagInput(name="invalid_tag"))


@pytest.mark.vcsp()
def test_create_group(vcsp_client, mock_server, vcsp_create_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_create_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.create_group(
            data_model=CreateGroupInput(
                name=test_group_name,
                credential_configuration_urn="urn:vcsp:credential_configurations:face:selfie:v1",
                description="test:group",
                expired_at="P1Y",
            ),
        )
        assert response.name == test_group_name
        assert response.credential_configuration_urn == mock_response["credential_configuration_urn"]
        assert response.size == mock_response["size"]
        assert response.description == mock_response["description"]
        assert response.expired_at == mock_response["expired_at"]
        assert response.created_at == mock_response["created_at"]
        assert response.updated_at == mock_response["updated_at"]


@pytest.mark.vcsp()
def test_vcsp_create_group_exception(
    vcsp_client, mock_server, vcsp_create_group_exception_parameters, test_group_name,
):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_create_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            input_model = CreateGroupInput(
                name=test_group_name,
                credential_configuration_urn="urn:vcsp:credential_configurations:face:selfie:v1",
                description="test:group",
                expired_at="P1Y",
            )
            with pytest.raises(exception):
                vcsp_client.create_group(data_model=input_model)


@pytest.mark.vcsp()
def test_get_groups(vcsp_client, mock_server, vcsp_get_groups_parameters, test_group_name, test_group_name_2):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_groups_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_groups(data_model=GetGroupsInput(name=test_group_name))
        assert response.items[0].name == test_group_name
        assert response.items[1].name == test_group_name_2
        assert response.total == 2   # noqa: PLR2004
        assert response.page == 1
        assert response.size == 100  # noqa: PLR2004
        assert response.pages == 1


@pytest.mark.vcsp()
def test_vcsp_get_group_exception(vcsp_client, mock_server, vcsp_get_group_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_get_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.get_group(data_model=GetGroupInput(name="nonexistent_group_name"))


@pytest.mark.vcsp()
def test_get_group(vcsp_client, mock_server, vcsp_get_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_group(data_model=GetGroupInput(name=test_group_name))
        assert response.name == test_group_name
        assert response.credential_configuration_urn == mock_response["credential_configuration_urn"]
        assert response.size == mock_response["size"]
        assert response.description == mock_response["description"]
        assert response.expired_at == mock_response["expired_at"]
        assert response.created_at == mock_response["created_at"]
        assert response.updated_at == mock_response["updated_at"]


@pytest.mark.vcsp()
def test_delete_group(vcsp_client, mock_server, vcsp_delete_group_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_delete_group_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_group(data_model=DeleteGroupInput(name=test_group_name))
        assert response is None


@pytest.mark.vcsp()
def test_vcsp_delete_group_exception(vcsp_client, mock_server, vcsp_delete_group_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_delete_group_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.delete_group(data_model=DeleteGroupInput(name="nonexistent_group_name"))


@pytest.mark.vcsp()
def test_get_group_members(vcsp_client, mock_server, vcsp_get_group_members_parameters, test_group_name):
    skip_if_not_mock(mock_server)

    for param in vcsp_get_group_members_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_group_members(data_model=GetGroupMembersInput(name=test_group_name))
        assert response.items[0].subject_id == mock_response["items"][0]["subject_id"]
        assert response.items[0].credential_id == mock_response["items"][0]["credential_id"]
        assert response.items[0].expired_in_group == mock_response["items"][0]["expired_in_group"]
        assert response.items[0].claims == mock_response["items"][0]["claims"]
        assert response.items[0].tags == mock_response["items"][0]["tags"]
        assert response.total == 2   # noqa: PLR2004
        assert response.page == 1
        assert response.size == 100  # noqa: PLR2004
        assert response.pages == 1


@pytest.mark.vcsp()
def test_vcsp_get_group_members_exception(vcsp_client, mock_server, vcsp_get_group_members_exception_parameters):
    skip_if_not_mock(mock_server)

    for exception_parameters in vcsp_get_group_members_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, exception = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

            with pytest.raises(exception):
                vcsp_client.get_group_members(data_model=GetGroupMembersInput(name="nonexistent_group_name"))
