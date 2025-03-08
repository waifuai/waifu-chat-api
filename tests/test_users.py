import pytest
import json
import sqlite3
import os
from src import waifuapi_db

TEST_DATABASE_FILE = "test_dialogs.db"

def test_create_user(client):
    """Test creating a user."""
    user_id = "test_user_1"
    response = client.put(f"/v1/user/id/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the user exists in the database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM dialogs WHERE current_user=? AND user_id=?', ("0_no_current_user_specified", user_id,))
    result = cursor.fetchone()
    assert result is not None
    conn.close()


def test_check_user_exists(client):
    """Test checking if a user exists."""
    user_id = "test_user_2"
    # First create the user
    client.put(f"/v1/user/id/{user_id}")

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
    client.put(f"/v1/user/id/{user_id}")

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
    client.put(f"/v1/user/id/{user_id}")

    response = client.delete(f"/v1/user/id/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the user is deleted from the database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT 1 FROM dialogs WHERE current_user=? AND user_id=?', ("0_no_current_user_specified", user_id,))
    result = cursor.fetchone()
    assert result is None
    conn.close()

    # Check deleting a non-existent user
    response = client.delete(f"/v1/user/id/non_existent_user")
    assert response.status_code == 404


def test_get_user_count(client):
    """Test getting the user count."""
    # Create some users
    client.put(f"/v1/user/id/test_user_5")
    client.put(f"/v1/user/id/test_user_6")

    response = client.get("/v1/user/all/count")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data['user_count'], int)
    assert data['user_count'] >= 2


def test_get_all_users_paged(client):
    """Test getting all users paged."""
    # Create some users
    client.put(f"/v1/user/id/test_user_7")
    client.put(f"/v1/user/id/test_user_8")
    client.put(f"/v1/user/id/test_user_9")

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
    client.put(f"/v1/user/id/{user_id}")

    # Try creating the user again
    response = client.put(f"/v1/user/id/{user_id}")
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