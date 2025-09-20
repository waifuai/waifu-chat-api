"""
Test suite for user management functionality in WaifuAPI.
This module contains comprehensive tests for user endpoints including creating,
checking existence, retrieving metadata, deleting users, and managing user lists.
Tests cover both successful operations and edge cases like non-existent users,
duplicate creation, and pagination functionality.
"""
import pytest
import json
import sqlite3
import os
from src import waifuapi_db

TEST_DATABASE_FILE = "test_dialogs.db"

def test_create_user(client):
    """Test creating a user."""
    user_id = "test_user_1"
    # Explicitly set Content-Type for PUT
    response = client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Verification will be done by test_check_user_exists


def test_check_user_exists(client):
    """Test checking if a user exists."""
    user_id = "test_user_2"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    response = client.get(f"/v1/user/id/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['exists'] == True
    assert json.loads(response.data)['user_id'] == user_id

    # Check for a non-existent user
    response = client.get(f"/v1/user/id/non_existent_user")
    assert response.status_code == 404
    assert json.loads(response.data)['exists'] == False
    assert json.loads(response.data)['user_id'] == "non_existent_user"


def test_get_user_metadata(client):
    """Test getting user metadata."""
    user_id = "test_user_3"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    response = client.get(f"/v1/user/metadata/{user_id}")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['user_id'] == user_id
    assert data['last_modified_datetime'] is not None
    assert data['last_modified_timestamp'] is not None

    # Check for a non-existent user
    response = client.get(f"/v1/user/metadata/non_existent_user")
    assert response.status_code == 404


def test_delete_user(client):
    """Test deleting a user."""
    user_id = "test_user_4"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    response = client.delete(f"/v1/user/id/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Verify deletion by checking the API endpoint
    response_check = client.get(f"/v1/user/id/{user_id}")
    assert response_check.status_code == 404

    # Check deleting a non-existent user
    response = client.delete(f"/v1/user/id/non_existent_user")
    assert response.status_code == 404


def test_get_user_count(client):
    """Test getting the user count."""
    # Create some users
    client.put(f"/v1/user/id/test_user_5", headers={'Content-Type': 'application/json'})
    client.put(f"/v1/user/id/test_user_6", headers={'Content-Type': 'application/json'})

    response = client.get("/v1/user/all/count")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data['user_count'], int)
    assert data['user_count'] >= 2


def test_get_all_users_paged(client):
    """Test getting all users paged."""
    # Create some users
    client.put(f"/v1/user/id/test_user_7", headers={'Content-Type': 'application/json'})
    client.put(f"/v1/user/id/test_user_8", headers={'Content-Type': 'application/json'})
    client.put(f"/v1/user/id/test_user_9", headers={'Content-Type': 'application/json'})

    response = client.get("/v1/user/all/id/0")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['page'] == 0
    assert isinstance(data['users'], list)
    assert len(data['users']) >= 3

def test_create_user_existing(client):
    """Test creating an existing user."""
    user_id = "test_user_1"
    # First create the user
    client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})

    # Try creating the user again
    response = client.put(f"/v1/user/id/{user_id}", headers={'Content-Type': 'application/json'})
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

def test_get_all_users_paged_empty(client):
    """Test getting all users paged when there are no users."""
    response = client.get("/v1/user/all/id/0")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['page'] == 0
    assert isinstance(data['users'], list)
    assert len(data['users']) == 0