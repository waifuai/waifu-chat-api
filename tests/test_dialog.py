import pytest
import json
import sqlite3
import os

TEST_DATABASE_FILE = "test_dialogs.db"

def test_reset_user_dialog(client):
    """Test resetting user dialog."""
    user_id = "test_user_10"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}")
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data)

    # Reset the dialog
    response = client.delete(f"/v1/user/dialog/{user_id}")
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is reset in the database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', ("0_no_current_user_specified", user_id,))
    result = cursor.fetchone()
    assert result[0] == ""
    conn.close()

    # Check resetting a non-existent user
    response = client.delete(f"/v1/user/dialog/non_existent_user")
    assert response.status_code == 404


def test_get_user_dialog_json(client):
    """Test getting user dialog in JSON format."""
    user_id = "test_user_11"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}")
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data)

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
    client.put(f"/v1/user/id/{user_id}")

    # Set the dialog
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    response = client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data)
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is set in the database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', ("0_no_current_user_specified", user_id,))
    result = cursor.fetchone()
    assert result[0] == 'User said: "Hello" Waifu said: "Hi"'
    conn.close()

    # Check setting dialog for a non-existent user
    response = client.put(f"/v1/user/dialog/json/non_existent_user", json=dialog_data)
    assert response.status_code == 404


def test_get_user_dialog_str(client):
    """Test getting user dialog as a string."""
    user_id = "test_user_13"
    # First create the user and add some dialog
    client.put(f"/v1/user/id/{user_id}")
    dialog_data = {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
    client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data)

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
    client.put(f"/v1/user/id/{user_id}")

    # Set the dialog
    dialog_data = {"dialog": []}
    response = client.put(f"/v1/user/dialog/json/{user_id}", json=dialog_data)
    assert response.status_code == 200
    assert json.loads(response.data)['user_id'] == user_id

    # Check if the dialog is set in the database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', ("0_no_current_user_specified", user_id,))
    result = cursor.fetchone()
    assert result[0] == ''
    conn.close()