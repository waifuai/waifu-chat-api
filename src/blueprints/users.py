from flask import Blueprint, request, Response
import json
import os
from typing import Dict, Any

from ..waifuapi_logging import get_logger, handle_exception, create_error_response
from ..waifuapi_validation import validate_user_id
from ..waifuapi_db_pool import (
    add_user_to_db, is_user_id_in_db, delete_user_from_db,
    get_user_count, get_all_users_paged, get_user_last_modified_datetime,
    get_user_last_modified_timestamp
)

users_bp = Blueprint('users', __name__)

logger = get_logger("users")
DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"

# v1 Create user
@users_bp.route('/id/<user_id>', methods=['PUT'])
def create_user_id(user_id: str) -> Response:
    """Creates a new user.

    Args:
        user_id (str): The ID of the user to create.

    Returns:
        Response: A JSON response containing the user ID.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.info(f"Creating user: {validated_user_id} for current_user: {current_user}")

        # Check if user already exists
        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            add_user_to_db(current_user=current_user, user_id=validated_user_id)
            logger.info(f"User created successfully: {validated_user_id}")
        else:
            logger.info(f"User already exists: {validated_user_id}")

        response_body: Dict[str, Any] = {'user_id': validated_user_id}
        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error creating user: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# v1 Check user exists
@users_bp.route('/id/<user_id>', methods=['GET'])
def check_user_id(user_id: str) -> Response:
    """Checks if a user exists.

    Args:
        user_id (str): The ID of the user to check.

    Returns:
        Response: A JSON response containing the user ID and a boolean indicating whether the user exists.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.debug(f"Checking if user exists: {validated_user_id}")

        exists = is_user_id_in_db(current_user=current_user, user_id=validated_user_id)

        response_body: Dict[str, Any] = {
            'user_id': validated_user_id,
            'exists': exists
        }

        status_code = 200 if exists else 404
        logger.debug(f"User {validated_user_id} exists: {exists}")

        return Response(
            json.dumps(response_body),
            status=status_code,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error checking user: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# v1 Get user metadata
@users_bp.route('/metadata/<user_id>', methods=['GET'])
def get_user_metadata(user_id: str) -> Response:
    """Gets user metadata (last modified datetime and timestamp).

    Args:
        user_id (str): The ID of the user.

    Returns:
        Response: A JSON response containing the user ID, last modified datetime, and last modified timestamp.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.debug(f"Getting metadata for user: {validated_user_id}")

        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            response_body: Dict[str, Any] = {
                'user_id': validated_user_id,
                'last_modified_datetime': None,
                'last_modified_timestamp': None
            }
            return Response(
                json.dumps(response_body),
                status=404,
                mimetype='application/json'
            )

        # Get user metadata
        last_modified_datetime = get_user_last_modified_datetime(current_user, validated_user_id)
        last_modified_timestamp = get_user_last_modified_timestamp(current_user, validated_user_id)

        response_body = {
            'user_id': validated_user_id,
            'last_modified_datetime': last_modified_datetime,
            'last_modified_timestamp': last_modified_timestamp
        }

        logger.debug(f"Retrieved metadata for user: {validated_user_id}")
        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error getting user metadata: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# v1 Delete user
@users_bp.route('/id/<user_id>', methods=['DELETE'])
def delete_user_id(user_id: str) -> Response:
    """Deletes a user.

    Args:
        user_id (str): The ID of the user to delete.

    Returns:
        Response: A JSON response containing the user ID.
    """
    try:
        # Validate user_id
        validated_user_id = validate_user_id(user_id)

        current_user: str = request.headers.get('current-user')
        if not current_user:
            current_user = DEFAULT_CURRENT_USER

        logger.info(f"Deleting user: {validated_user_id}")

        if not is_user_id_in_db(current_user=current_user, user_id=validated_user_id):
            response_body: Dict[str, Any] = {'user_id': validated_user_id}
            return Response(
                json.dumps(response_body),
                status=404,
                mimetype='application/json'
            )

        delete_user_from_db(current_user=current_user, user_id=validated_user_id)

        response_body = {'user_id': validated_user_id}
        logger.info(f"User deleted successfully: {validated_user_id}")

        return Response(
            json.dumps(response_body),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        error_response = handle_exception(e, logger, f"Error deleting user: {user_id}")
        return Response(
            json.dumps(error_response),
            status=error_response.get("error", {}).get("status_code", 500),
            mimetype='application/json'
        )


# v1 Get users count
@users_bp.route('/all/count', methods=['GET'])
def get_user_count() -> str:
    """Gets the total number of users.

    Returns:
        str: A JSON string containing the user count.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# v1 Get all users paged by hundreds
@users_bp.route('/all/id/<int:page>', methods=['GET'])
def get_all_users_paged(page: int) -> str:
    """Gets a page of users (hundreds per page).

    Args:
        page (int): The page number.

    Returns:
        str: A JSON string containing the page number and a list of user IDs.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("current_user to get is:", current_user)
    response_body: dict = {
        'page': page,
        'users': waifuapi_db.get_all_users_paged(current_user=current_user, page=page)
    }
    response_body_str: str = json.dumps(response_body)
    try:
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')