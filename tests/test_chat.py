import pytest
import json

def test_send_chat_message_form(client, monkeypatch):
    """Test sending a chat message using form data."""
    # Mock the waifuapi_process.process_form_dict function
    def mock_process_form_dict(current_user, form_dict):
        return "Mocked response"

    monkeypatch.setattr("src.blueprints.chat.process_chat_message", mock_process_form_dict)

    user_id = "test_user_14"
    message = "Hello"
    response = client.post(f"/path?message={message}&user_id={user_id}")
    assert response.status_code == 200
    assert response.data.decode('utf-8') == "Mocked response"


def test_send_chat_message_json(client, monkeypatch):
    """Test sending a chat message using JSON data."""
    # Mock the waifuapi_process.process_form_dict function
    def mock_process_form_dict(current_user, form_dict):
        return "Mocked response"

    monkeypatch.setattr("src.blueprints.chat.process_chat_message", mock_process_form_dict)

    user_id = "test_user_15"
    message = "Hello"
    data = {"user_id": user_id, "message": message}
    response = client.post("/v1/waifu", json=data)
    assert response.status_code == 200
    assert json.loads(response.data)['response'] == "Mocked response"
    assert json.loads(response.data)['user_id'] == user_id

def test_send_chat_message_form_no_user(client, monkeypatch):
    """Test sending a chat message using form data without user_id."""
    # Mock the waifuapi_process.process_form_dict function
    def mock_process_form_dict(current_user, form_dict):
        return "Mocked response"

    monkeypatch.setattr("src.blueprints.chat.process_chat_message", mock_process_form_dict)

    message = "Hello"
    response = client.post(f"/path?message={message}")
    assert response.status_code == 200
    assert response.data.decode('utf-8') == "Mocked response"

def test_send_chat_message_json_no_message(client, monkeypatch):
    """Test sending a chat message using JSON data without message."""
    # Mock the waifuapi_process.process_form_dict function
    def mock_process_form_dict(current_user, form_dict):
        return "Mocked response"

    monkeypatch.setattr("src.blueprints.chat.process_chat_message", mock_process_form_dict)

    user_id = "test_user_15"
    data = {"user_id": user_id}
    response = client.post("/v1/waifu", json=data)
    assert response.status_code == 200
    assert json.loads(response.data)['response'] == "Mocked response"
    assert json.loads(response.data)['user_id'] == user_id