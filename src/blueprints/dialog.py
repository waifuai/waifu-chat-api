from flask import Blueprint, request, Response
import json
import re
import waifuapi_db
import waifuapi_process

dialog_bp = Blueprint('dialog', __name__)

DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"


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
@dialog_bp.route('/json/<user_id>', methods=['GET'])
def get_user_dialog(user_id: str) -> str:
    """Gets the user's dialog history as a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID and the dialog history.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
            return Response(response_body_str, status=200, mimetype='application/json')
        else:
            return Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# Set user dialog json
@dialog_bp.route('/json/<user_id>', methods=['PUT'])
def update_user_dialog(user_id: str) -> str:
    """Updates the user's dialog history with a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    response_body: dict = {
        'user_id': user_id
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            print("user_id to update is:", user_id)
            dialog_json: dict = request.json
            print('dialog_json:', dialog_json)
            dialog_str: str = json_to_dialog(dialog_json)
            print('dialog_str:', dialog_str)
            waifuapi_db.update_user_dialog(current_user=current_user, user_id=user_id, dialog=dialog_str)
            return Response(response_body_str, status=200, mimetype='application/json')
        else:
            return Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# Get user dialog string
@dialog_bp.route('/str/<user_id>', methods=['GET'])
def get_user_dialog_str(user_id: str) -> str:
    """Gets the user's dialog history as a string.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID and the dialog history.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
            return Response(response_body_str, status=200, mimetype='application/json')
        else:
            return Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# v1 resetUserDialog
@dialog_bp.route('/<user_id>', methods=['DELETE'])
def reset_user_chat(user_id: str) -> str:
    """Resets the user's dialog history.

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to reset is:", user_id)
    response_body: dict = {
        'user_id': user_id
    }
    response_body_str: str = json.dumps(response_body)
    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            return Response(response_body_str, status=404, mimetype='application/json')
        waifuapi_db.reset_user_chat(current_user=current_user, user_id=user_id)
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')