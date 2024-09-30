from vericlient import VcspClient


def test_vcsp_alive(mock_server, vcsp_alive_parameters):
    for param in vcsp_alive_parameters:
        endpoint, mock_response, mock_status_code, url, environment, location, _ = param
        if mock_server:
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)

        vcsp_client = VcspClient(
            apikey="fake-apikey",
            environment=environment,
            location=location,
            url=url,
        )
        response = vcsp_client.alive()

        assert response
