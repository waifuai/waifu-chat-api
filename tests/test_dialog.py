"""
Test suite for dialog functionality in WaifuAPI.
This module contains tests for dialog management endpoints including getting
dialog in JSON and string formats, setting dialog from JSON, resetting dialog
history, and handling edge cases like non-existent users and empty dialogs.
Tests verify proper database operations and API responses.
"""
import pytest
import json
import sqlite3
import os

TEST_DATABASE_FILE = "test_dialogs.db"

def test_reset_user_dialog(client):
    """Test resetting user dialog."""
    user_id = "test_user_10"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data, headers={'Content-Type': 'application/json'})

    # Reset the dialog
    response = client.delete(f"/v1/user/dialog/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is reset using the API
    response_check = client.get(f"/v1/user/dialog/str/{user_id}")
    assert response_check.status_code == 200
    assert json.loads(response_check.data)['dialog'] == ""

    # Check resetting a non-existent user
    response = client.delete(f"/v1/user/dialog/non_existent_user")
    assert response.status_code == 404


def test_get_user_dialog_json(client):
    """Test getting user dialog in JSON format."""
    user_id = "test_user_11"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data, headers={'Content-Type': 'application/json'})

    # Get the dialog
    response = client.get(f"/v1/user/dialog/json/{user_id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user_id'] == user_id
    assert data['dialog'] == dialog_data['dialog']

    # Check for a non-existent user
    response = client.get(f"/v1/user/dialog/json/non_existent_user")
    assert response.status_code == 404


def test_set_user_dialog_json(client):
    """Test setting user dialog in JSON format."""
    user_id = "test_user_12"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    # Set the dialog
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    response = client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data, headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is set using the API
    response_check = client.get(f"/v1/user/dialog/str/{user_id}")
    assert response_check.status_code == 200
    assert json.loads(response_check.data)['dialog'] == 'User said: "Hello" Waifu said: "Hi"'

    # Check setting dialog for a non-existent user
    response = client.put(f"/v1/user/dialog/json/non_existent_user", json=dialog_data, headers={'Content-Type': 'application/json'})
    assert response.status_code == 404


def test_get_user_dialog_str(client):
    """Test getting user dialog as a string."""
    user_id = "test_user_13"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data, headers={'Content-Type': 'application/json'})

    # Get the dialog
    response = client.get(f"/v1/user/dialog/str/{user_id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user_id'] == user_id
    assert data['dialog'] == 'User said: "Hello" Waifu said: "Hi"'

    # Check for a non-existent user
    response = client.get(f"/v1/user/dialog/str/non_existent_user")
    assert response.status_code == 404

def test_reset_user_dialog_nonexistent(client):
    """Test resetting dialog for a non-existent user."""
    user_id = "non_existent_user"
    response = client.delete(f"/v1/user/dialog/{user_id}")
    assert response.status_code == 404

def test_get_user_dialog_json_nonexistent(client):
    """Test getting dialog in JSON format for a non-existent user."""
    user_id = "non_existent_user"
    response = client.get(f"/v1/user/dialog/json/{user_id}")
    assert response.status_code == 404

def test_set_user_dialog_json_empty(client):
    """Test setting user dialog in JSON format with empty dialog."""
    user_id = "test_user_12"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    # Set the dialog
    dialog_data = {"dialog": []}
    response = client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data, headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is set using the API
    response_check = client.get(f"/v1/user/dialog/str/{user_id}")
    assert response_check.status_code == 200
    assert json.loads(response_check.data)['dialog'] == ''