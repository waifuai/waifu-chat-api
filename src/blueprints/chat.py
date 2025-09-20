"""
Chat blueprint module for WaifuAPI.
This module defines Flask routes for handling chat messages, both through form data
(POST /path) and JSON data (POST /v1/waifu). It provides endpoints for users to
send messages to the AI model and receive responses, with proper validation,
error handling, and logging.
"""
from flask import Blueprint, request, Response
import json
import waifuapi_process
from ..waifuapi_validation import validate_form_dict, ValidationError
from ..waifuapi_logging import get_logger, handle_exception, create_error_response
from ..waifuapi_config import get_app_config

chat_bp = Blueprint('chat', __name__)

logger = get_logger("chat")
DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"


def process_chat_message(form_dict: dict) -> str:
    """Handles chat message requests (using form or JSON data).

    Returns:
        str: The AI's response message.
    """
    try:
        config = get_app_config()
        default_msg = config.default_response
    except Exception:
        default_msg = "The AI model is currently unavailable. Please try again later."

    # Get current user from headers
    current_user: str = request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER

    try:
        # Validate form data
        validated_form_dict = validate_form_dict(form_dict)
        logger.debug(f"Processing validated form data for user: {current_user}")

        # Process the chat message
        response: str = waifuapi_process.process_form_dict(
            current_user=current_user,
            form_dict=validated_form_dict
        )

        # Check for temporary error messages
        if response == "error":
            logger.warning(f"Temporary error for user {current_user}")
            response = "Temporary error, please try again in 30 seconds."

        return response

    except ValidationError as e:
        logger.warning(f"Validation error for user {current_user}: {e}")
        return default_msg
    except Exception as e:
        error_response = handle_exception(e, logger, f"Chat processing error for user {current_user}")
        return default_msg


# v1 Send chat message
@chat_bp.route('/path', methods=['POST'])
def main() -> Response:
    """Handles chat message requests (using form data).

    Returns:
        Response: The AI's response message.
    """
    try:
        form_dict: dict = request.args.to_dict()
        if not form_dict:
            form_dict = {}

        response_text = process_chat_message(form_dict=form_dict)
        logger.info("Chat message processed successfully via form data")
        return Response(response_text, status=200, mimetype='text/plain')

    except Exception as e:
        error_response = handle_exception(e, logger, "Form chat endpoint error")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# v1 Send chat message
@chat_bp.route('/v1/waifu', methods=['POST'])
def waifu() -> Response:
    """Handles chat message requests (using JSON data).

    Returns:
        Response: A JSON response containing the user ID and the AI's response.
    """
    try:
        form_dict: dict = request.get_json() or {}
        user_id: str = form_dict.get('user_id', '')
        username: str = form_dict.get('username', '')
        message: str = form_dict.get('message', '')
        from_name: str = form_dict.get('from_name', '')
        to_name: str = form_dict.get('to_name', '')
        situation: str = form_dict.get('situation', '')
        translate_from: str = form_dict.get('translate_from', '')
        translate_to: str = form_dict.get('translate_to', '')

        response: str = process_chat_message(form_dict=form_dict)

        response_json: dict = {
            "user_id": user_id,
            "response": response
        }

        logger.info(f"Chat message processed successfully for user: {user_id}")
        return Response(
            json.dumps(response_json),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, "JSON chat endpoint error")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )