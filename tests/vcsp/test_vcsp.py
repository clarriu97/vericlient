import pytest
from vericlient.vcsp.exceptions import (
    AssuranceMethodNotFoundError,
)
from vericlient.vcsp.models import (
    AssuranceMethodInput,
)


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
