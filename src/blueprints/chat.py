from flask import Blueprint, request, Response
import json
import waifuapi_process
import os
from dotenv import load_dotenv
load_dotenv()

chat_bp = Blueprint('chat', __name__)

DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"
DEFAULT_MSG: str = os.environ.get("DEFAULT_RESPONSE", "The AI model is currently unavailable. Please try again later.")


def process_chat_message(form_dict: dict) -> str:
    """Handles chat message requests (using form or JSON data).

    Returns:
        str: The AI's response message.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
@chat_bp.route('/path', methods=['POST'])
def main() -> str:
    """Handles chat message requests (using form data).

    Returns:
        str: The AI's response message.
    """
    form_dict: dict = request.args.to_dict()
    if not form_dict:
        form_dict = {}
    return process_chat_message(form_dict=form_dict)


# v1 Send chat message
@chat_bp.route('/v1/waifu', methods=['POST'])
def waifu() -> str:
    """Handles chat message requests (using JSON data).

    Returns:
        str: A JSON string containing the user ID and the AI's response.
    """
    form_dict: dict = request.json
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
    return Response(response_json_string, status=200, mimetype='application/json')