"""
Dialog blueprint module for WaifuAPI.
This module defines Flask routes for managing user dialog history, including
getting dialog in JSON or string format, setting dialog from JSON, and resetting
dialog history. It provides endpoints for users to manage their conversation
history with proper validation, error handling, and database operations.
"""
from flask import Blueprint, request, Response
import json
import re
from typing import Dict, Any, List

from ..waifuapi_logging import get_logger, handle_exception, create_error_response
from ..waifuapi_validation import validate_user_id, validate_dialog_json, ValidationError
from ..waifuapi_db_pool import (
    get_user_dialog, update_user_dialog, is_user_id_in_db,
    reset_user_chat, get_old_dialog
)

dialog_bp = Blueprint('dialog', __name__)

logger = get_logger("dialog")
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
def get_user_dialog_json(user_id: str) -> Response:
    """Gets the user's dialog history as a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        Response: A JSON response containing the user ID and the dialog history.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.debug(f"Getting dialog for user: {validated_user_id}")

        response_body: Dict[str, Any] = {
            'user_id': validated_user_id,
            'dialog': None
        }

        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            return Response(
                json.dumps(response_body),
                status=404,
                mimetype='application/json'
            )

        # Get and parse dialog
        dialog_str = get_user_dialog(current_user=current_user, user_id=validated_user_id)
        dialog_list = dialog_to_json(dialog=dialog_str)
        response_body["dialog"] = dialog_list

        logger.debug(f"Retrieved dialog with {len(dialog_list)} entries for user: {validated_user_id}")
        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error getting user dialog: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# Set user dialog json
@dialog_bp.route('/json/<user_id>', methods=['PUT'])
def update_user_dialog_json(user_id: str) -> Response:
    """Updates the user's dialog history with a JSON object.

    Args:
        user_id (str): The ID of the user.

    Returns:
        Response: A JSON response containing the user ID.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.debug(f"Updating dialog for user: {validated_user_id}")

        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            response_body: Dict[str, Any] = {'user_id': validated_user_id}
            return Response(
                json.dumps(response_body),
                status=404,
                mimetype='application/json'
            )

        # Validate and process dialog data
        dialog_json = request.get_json() or {}
        validated_dialog = validate_dialog_json({"dialog": dialog_json.get("dialog", [])})
        dialog_str = json_to_dialog({"dialog": validated_dialog})

        logger.debug(f"Updating dialog with {len(validated_dialog)} entries for user: {validated_user_id}")

        # Update the dialog
        update_user_dialog(current_user=current_user, user_id=validated_user_id, dialog=dialog_str)

        response_body = {'user_id': validated_user_id}
        logger.info(f"Dialog updated successfully for user: {validated_user_id}")

        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except ValidationError as e:
        logger.warning(f"Dialog validation error for user {user_id}: {e}")
        error_response = create_error_response(str(e), 400, "VALIDATION_ERROR")
        return Response(
            json.dumps(error_response),
            status=400,
            mimetype='application/json'
        )
    except Exception as e:
        error_response = handle_exception(e, logger, f"Error updating user dialog: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


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
def reset_user_chat_endpoint(user_id: str) -> Response:
    """Resets the user's dialog history.

    Args:
        user_id (str): The ID of the user.

    Returns:
        Response: A JSON response containing the user ID.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.info(f"Resetting dialog for user: {validated_user_id}")

        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            response_body: Dict[str, Any] = {'user_id': validated_user_id}
            return Response(
                json.dumps(response_body),
                status=404,
                mimetype='application/json'
            )

        # Reset the user's chat
        reset_user_chat(current_user=current_user, user_id=validated_user_id)

        response_body = {'user_id': validated_user_id}
        logger.info(f"Dialog reset successfully for user: {validated_user_id}")

        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error resetting user dialog: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )