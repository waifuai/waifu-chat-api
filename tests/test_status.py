import pytest
import json

def test_get_server_status(client):
    """Test getting the server status."""
    response = client.get("/v1/server/status")
    assert response.status_code == 200
    assert json.loads(response.data)['status'] == "ok"

def test_get_server_status_invalid_route(client):
    """Test getting the server status with an invalid route."""
    response = client.get("/v1/server/invalid")
    assert response.status_code == 404