from flask import Blueprint, request, Response
import json
import waifuapi_db
import waifuapi_process
import os

users_bp = Blueprint('users', __name__)

DEFAULT_CURRENT_USER: str = "0_no_current_user_specified"

# v1 Create user
@users_bp.route('/id/<user_id>', methods=['PUT'])
def create_user_id(user_id: str) -> str:
    """Creates a new user.

    Args:
        user_id (str): The ID of the user to create.

    Returns:
        str: A JSON string containing the user ID.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
    if not current_user:
        current_user = DEFAULT_CURRENT_USER
    print("user_id to create is:", user_id)
    response_body: dict = {'user_id': user_id}
    response_body_str: str = json.dumps(response_body)
    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            waifuapi_db.add_user_to_db(current_user=current_user, user_id=user_id)
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# v1 Check user exists
@users_bp.route('/id/<user_id>', methods=['GET'])
def check_user_id(user_id: str) -> str:
    """Checks if a user exists.

    Args:
        user_id (str): The ID of the user to check.

    Returns:
        str: A JSON string containing the user ID and a boolean indicating whether the user exists.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
            return Response(response_body_str, status=200, mimetype='application/json')
        else:
            return Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        response_body['exists'] = None
        response_body_str = json.dumps(response_body)
        return Response(response_body_str, status=400, mimetype='application/json')


# v1 Get user metadata
# get the user metadata - last modified datetime and last modified timestamp
@users_bp.route('/metadata/<user_id>', methods=['GET'])
def get_user_metadata(user_id: str) -> str:
    """Gets user metadata (last modified datetime and timestamp).

    Args:
        user_id (str): The ID of the user.

    Returns:
        str: A JSON string containing the user ID, last modified datetime, and last modified timestamp.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=request)
 # Commented out for testing

    current_user: str = request.headers.get('current-user')
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
            return Response(response_body_str, status=200, mimetype='application/json')
        else:
            return Response(response_body_str, status=404, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


# v1 Delete user
@users_bp.route('/id/<user_id>', methods=['DELETE'])
def delete_user_id(user_id: str) -> str:
    """Deletes a user.

    Args:
        user_id (str): The ID of the user to delete.

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
        waifuapi_db.delete_user_from_db(current_user=current_user, user_id=user_id)
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')


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