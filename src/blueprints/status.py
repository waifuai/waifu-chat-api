from flask import Blueprint, Response
import json
import waifuapi_process

status_bp = Blueprint('status', __name__)


# v1 Check server status
@status_bp.route('/status', methods=['GET'])
def get_server_status() -> str:
    """Checks the server status.

    Returns:
        str: A JSON string containing the status.
    """
    # waifuapi_process.print_flask_request_info(flask_request_object=None)
 # Commented out for testing

    response_body: dict = {'status': 'ok'}
    response_body_str: str = json.dumps(response_body)
    try:
        return Response(response_body_str, status=200, mimetype='application/json')
    except Exception as e:
        print(e)
        return Response(response_body_str, status=400, mimetype='application/json')