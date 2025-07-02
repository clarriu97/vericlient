
import pytest
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)
from vericlient.vcsp.models import (
    Applicant,
    AssuranceMethodInput,
    DeleteAccountInput,
    DeleteCredentialInput,
    EnrollmentInput,
    GetAccountInput,
    GetCredentialInput,
    GetCredentialsInput,
)


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
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for exception_parameters in vcsp_enrollment_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, environment, location, exception = param
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
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for param in vcsp_get_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.get_account(data_model=GetAccountInput(subject_id=test_subject_id))
        assert response.subject_id == test_subject_id


@pytest.mark.vcsp()
def test_delete_account(vcsp_client, mock_server, vcsp_delete_account_parameters, test_subject_id):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for param in vcsp_delete_account_parameters:
        endpoint, mock_response, mock_status_code, _, _, _, _ = param
        mock_server.delete(endpoint, json=mock_response, status_code=mock_status_code)

        response = vcsp_client.delete_account(data_model=DeleteAccountInput(subject_id=test_subject_id))
        assert response is None


@pytest.mark.vcsp()
def test_get_all_credentials(vcsp_client, mock_server, vcsp_get_all_credentials_parameters, test_subject_id):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

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
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

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
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

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
