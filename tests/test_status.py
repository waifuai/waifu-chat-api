"""
Test suite for server status functionality in WaifuAPI.
This module contains tests for status endpoints including checking server
health and handling invalid routes. Tests verify that the API properly
reports server status and handles error cases appropriately.
"""
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