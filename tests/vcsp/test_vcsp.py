import pytest
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)
from vericlient.vcsp.models import (
    AssuranceMethodInput,
)
from vericlient import VcspClient
from vericlient.vcsp.models import (
    Applicant,
    EnrollmentInput,
    EnrollmentOutput,
    GetAccountInput,
    GetCredentialInput,
    DeleteSubjectInput,
    AssuranceMethodInput,
)
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)
import pytest
import uuid


def test_vcsp_alive(vcsp_client, mock_server, vcsp_alive_parameters):
    if mock_server:
        for param in vcsp_alive_parameters:
            endpoint, mock_response, mock_status_code, _, _, _, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

    response = vcsp_client.alive()
    assert response


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


def test_mock_vcsp_enroll_subject(vcsp_client, mock_server, vcsp_enrollment_parameters, audio_file_path):
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
        assert response.subject_id == "fake-subject_id"


def test_vcsp_enrollment_exception(mock_server, vcsp_enrollment_exception_parameters, audio_file_path):
    if not mock_server:
        pytest.skip("This test only runs in mock mode")

    for exception_parameters in vcsp_enrollment_exception_parameters:
        for param in exception_parameters:
            endpoint, mock_response, mock_status_code, _, environment, location, exception = param
            mock_server.post(endpoint, json=mock_response, status_code=mock_status_code)

            vcsp_client = VcspClient(
                apikey="fake-apikey",
                environment=environment,
                location=location,
            )

            with pytest.raises(exception):
                input_model = EnrollmentInput(
                    sample=audio_file_path,
                    applicant=Applicant(
                        credential_configuration_urn="fake-credential_configuration_urn",
                        assurance_method_urn="fake-assurance_method_urn",
                        assurance={},
                    ),
                )
                vcsp_client.enroll_subject(data_model=input_model)
