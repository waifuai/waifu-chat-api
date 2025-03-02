from dotenv import load_dotenv
load_dotenv()

import time
import random
import json
import os

import flask
import waifuapi_process
import waifuapi_db

app = flask.Flask(__name__)

DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"
DEFAULT_MSG: str = os.environ.get("DEFAULT_RESPONSE", "The AI model is currently unavailable. Please try again later.")


def process_chat_message(form_dict: dict) -> str:
    """Handles chat message requests (using form or JSON data).

    Returns:
        str: The AI's response message.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER

    try:
        response: str = waifuapi_process.process_form_dict(current_user=current_user, form_dict=form_dict)
        TEMP_ERROR_MSG: str = "error"
        if response == TEMP_ERROR_MSG:
            print(f"error: {TEMP_ERROR_MSG}")
            response = "Temporary error, please try again in 30 seconds."

    except Exception as e:
        print(e)
        response = DEFAULT_MSG
    return response


# v1 Send chat message
@app.route('/path', methods=['POST'])
def main() -> str:
    """Handles chat message requests (using form data).

    Returns:
        str: The AI's response message.
    """
    form_dict: dict = flask.request.args.to_dict()
    if not form_dict:
        form_dict = {}
    return process_chat_message(form_dict=form_dict)


# v1 Send chat message
@app.route('/v1/waifu', methods=['POST'])
def waifu() -> str:
    """Handles chat message requests (using JSON data).

    Returns:
        str: A JSON string containing the user ID and the AI's response.
    """
    form_dict: dict = flask.request.json
    if not form_dict:
        form_dict = {}
    user_id: str = form_dict.get('user_id')
    username: str = form_dict.get('username')
    message: str = form_dict.get('message')
    from_name: str = form_dict.get('from_name')
    to_name: str = form_dict.get('to_name')
    situation: str = form_dict.get('situation')
    translate_from: str = form_dict.get('translate_from')
    translate_to: str = form_dict.get('translate_to')

    response: str = process_chat_message(form_dict=form_dict)

    response_json: dict = {
        "user_id": user_id,
        "response": response
    }
    response_json_string: str = json.dumps(response_json)
    return flask.Response(response_json_string, status=200, mimetype='application/json')


# v1 Create user
@app.route('/v1/user/id/<user_id>', methods=['PUT'])
def create_user_id(user_id: str) -> str:
    """Creates a new user.

    Args:
        user_id (str): The ID of the user to create.

    Returns:
        str: A JSON string containing the user ID.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to create is:", user_id)
    response_body: dict = {'user_id': user_id}
    response_body_str: str = json.dumps(response_body)
    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            waifuapi_db.add_user_to_db(current_user=current_user, user_id=user_id)
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# v1 Check user exists
@app.route('/v1/user/id/<user_id>', methods=['GET'])
def check_user_id(user_id: str) -> str:
    """Checks if a user exists.

    Args:
        user_id (str): The ID of the user to check.

    Returns:
        str: A JSON string containing the user ID and a boolean indicating whether the user exists.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to check is:", user_id)
    response_body: dict = {
        'user_id': user_id,
        'exists': False
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            response_body['exists'] = True
            response_body_str = json.dumps(response_body)
            return flask.Response(response_body_str, status=200, mimetype='application/json')
        else:
            return flask.Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        response_body['exists'] = None
        response_body_str = json.dumps(response_body)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# v1 Get user metadata
# get the user metadata - last modified datetime and last modified timestamp
@app.route('/v1/user/metadata/<user_id>', methods=['GET'])
def get_user_metadata(user_id: str) -> str:
    """Gets user metadata (last modified datetime and timestamp).

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID, last modified datetime, and last modified timestamp.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    response_body: dict = {
        'user_id': user_id,
        'last_modified_datetime': None,
        'last_modified_timestamp': None
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            print("user_id to get is:", user_id)
            last_modified_datetime_str: str = waifuapi_db.get_user_last_modified_datetime(current_user=current_user, user_id=user_id)
            last_modified_timestamp_str: str = waifuapi_db.get_user_last_modified_timestamp(current_user=current_user, user_id=user_id)
            response_body = {
                'user_id': user_id,
                'last_modified_datetime': last_modified_datetime_str,
                'last_modified_timestamp': last_modified_timestamp_str
            }
            response_body_str = json.dumps(response_body)
            return flask.Response(response_body_str, status=200, mimetype='application/json')
        else:
            return flask.Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# v1 Delete user
@app.route('/v1/user/id/<user_id>', methods=['DELETE'])
def delete_user_id(user_id: str) -> str:
    """Deletes a user.

    Args:
        user_id (str): The ID of the user to delete.

    Returns:
        str: A JSON string containing the user ID.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to reset is:", user_id)
    response_body: dict = {
        'user_id': user_id
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            return flask.Response(response_body_str, status=404, mimetype='application/json')
        waifuapi_db.delete_user_from_db(current_user=current_user, user_id=user_id)
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


################### User identity ###################


# v1 resetUserDialog
@app.route('/v1/user/dialog/<user_id>', methods=['DELETE'])
def reset_user_chat(user_id: str) -> str:
    """Resets the user's dialog history.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to reset is:", user_id)
    response_body: dict = {
        'user_id': user_id
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            return flask.Response(response_body_str, status=404, mimetype='application/json')
        waifuapi_db.reset_user_chat(current_user=current_user, user_id=user_id)
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


################### User dialog ###################

def dialog_to_json(dialog: str) -> list[dict]:
    """Converts a dialog string to a JSON object.

    Args:
        dialog (str): The dialog string.  Example: "User said: \"first\" Waifu said: \"second\""

    Returns:
        list[dict]: A JSON object representing the dialog.  Example:
             [{"index": 0, "name": "User", "message": "first"},
              {"index": 1, "name": "Waifu", "message": "second"}]
    """
    output = []
    # Find all occurrences of the pattern "Name said: "message""
    matches = re.findall(r'([^"]+)\s+said:\s+"([^"]+)"', dialog)

    for index, (name, message) in enumerate(matches):
        output.append({
            "index": index,
            "name": name.strip(),
            "message": message
        })
    return output


def json_to_dialog(json_obj: dict) -> str:
    """Converts a JSON object representing a dialog to a string.

    Args:
        json_obj (dict): The JSON object.

    Returns:
        str: The dialog string.
    """
    dialog = json_obj["dialog"]
    dialog_strings = [
        f'{entry["name"]} said: "{entry["message"]}"' for entry in dialog
    ]
    return " ".join(dialog_strings)


# Get user dialog json
@app.route('/v1/user/dialog/json/<user_id>', methods=['GET'])
def get_user_dialog(user_id: str) -> str:
    """Gets the user's dialog history as a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID and the dialog history.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER

    response_body: dict = {
        'user_id': user_id,
        'dialog': None
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            print("user_id to get is:", user_id)
            dialog_str: str = waifuapi_db.get_user_dialog(current_user=current_user, user_id=user_id)
            dialog_list: list = dialog_to_json(dialog=dialog_str)
            response_body["dialog"] = dialog_list
            response_body_str = json.dumps(response_body)
            return flask.Response(response_body_str, status=200, mimetype='application/json')
        else:
            return flask.Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# Set user dialog json
@app.route('/v1/user/dialog/json/<user_id>', methods=['PUT'])
def update_user_dialog(user_id: str) -> str:
    """Updates the user's dialog history with a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    response_body: dict = {
        'user_id': user_id
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            print("user_id to update is:", user_id)
            dialog_json: dict = flask.request.json
            print('dialog_json:', dialog_json)
            dialog_str: str = json_to_dialog(dialog_json)
            print('dialog_str:', dialog_str)
            waifuapi_db.update_user_dialog(current_user=current_user, user_id=user_id, dialog=dialog_str)
            return flask.Response(response_body_str, status=200, mimetype='application/json')
        else:
            return flask.Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# Get user dialog string
@app.route('/v1/user/dialog/str/<user_id>', methods=['GET'])
def get_user_dialog_str(user_id: str) -> str:
    """Gets the user's dialog history as a string.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID and the dialog history.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    response_body: dict = {
        'user_id': user_id,
        'dialog': None
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            print("user_id to get is:", user_id)
            dialog_str: str = waifuapi_db.get_user_dialog(current_user=current_user, user_id=user_id)
            response_body = {
                'user_id': user_id,
                'dialog': dialog_str
            }
            response_body_str = json.dumps(response_body)
            return flask.Response(response_body_str, status=200, mimetype='application/json')
        else:
            return flask.Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


###################### Users management ######################


# v1 Get users count
@app.route('/v1/user/all/count', methods=['GET'])
def get_user_count() -> str:
    """Gets the total number of users.

    Returns:
        str: A JSON string containing the user count.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("current_user to get is:", current_user)
    response_body: dict = {'user_count': None}
    response_body_str: str = json.dumps(response_body)
    try:
        response_body = {
            'user_count': waifuapi_db.get_user_count(current_user=current_user)
        }
        response_body_str = json.dumps(response_body)
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# v1 Get all users paged by hundreds
@app.route('/v1/user/all/id/<int:page>', methods=['GET'])
def get_all_users_paged(page: int) -> str:
    """Gets a page of users (hundreds per page).

    Args:
        page (int): The page number.

    Returns:
        str: A JSON string containing the page number and a list of user IDs.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    current_user: str = flask.request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("current_user to get is:", current_user)
    response_body: dict = {
        'page': page,
        'users': waifuapi_db.get_all_users_paged(current_user=current_user, page=page)
    }
    response_body_str: str = json.dumps(response_body)
    try:
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')


# v1 Check server status
@app.route('/v1/server/status', methods=['GET'])
def get_server_status() -> str:
    """Checks the server status.

    Returns:
        str: A JSON string containing the status.
    """
    waifuapi_process.print_flask_request_info(flask_request_object=flask.request)

    response_body: dict = {'status': 'ok'}
    response_body_str: str = json.dumps(response_body)
    try:
        return flask.Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return flask.Response(response_body_str, status=400, mimetype='application/json')
