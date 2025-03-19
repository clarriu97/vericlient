

def test_vcsp_alive(vcsp_client, mock_server, vcsp_alive_parameters):
    if mock_server:
        for param in vcsp_alive_parameters:
            endpoint, mock_response, mock_status_code, url, environment, location, _ = param
            mock_server.get(endpoint, json=mock_response, status_code=mock_status_code)
    
    response = vcsp_client.alive()
    assert response
