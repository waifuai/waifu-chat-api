import os
import flask
from dotenv import load_dotenv

# Import blueprints
from .blueprints.users import users_bp
from .blueprints.dialog import dialog_bp
from .blueprints.status import status_bp
from .blueprints.chat import chat_bp

# Import new modules
from .waifuapi_config import init_app_config, get_app_config
from .waifuapi_logging import setup_logging, get_logger

def create_app(config_override=None):
    """Creates and configures the Flask application."""
    app = flask.Flask(__name__)

    # Load environment variables from .env file first
    load_dotenv()

    # Initialize configuration
    try:
        config = init_app_config()
        logger = setup_logging()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        # Fallback to basic config
        config = type('Config', (), {
            'database_file': 'dialogs.db',
            'port': 5000,
            'debug': False
        })()

    # Apply configuration to Flask app
    app.config.from_mapping(
        DATABASE_FILE=config.database_file,
        SECRET_KEY=config.secret_key or os.urandom(24),
        DEBUG=config.debug
    )

    # Override config with provided dictionary (for testing)
    if config_override:
        app.config.from_mapping(config_override)

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Ensure logs directory exists
    try:
        os.makedirs("logs")
    except OSError:
        pass

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix='/v1/user')
    app.register_blueprint(dialog_bp, url_prefix='/v1/user/dialog')
    app.register_blueprint(status_bp, url_prefix='/v1/server')
    app.register_blueprint(chat_bp)

    # Initialize database connection pool
    from .waifuapi_db_pool import init_db_pool, init_database_tables, close_db
    init_db_pool()
    init_database_tables()
    app.teardown_appcontext(close_db)

    # Add error handlers
    @app.errorhandler(400)
    def bad_request(error):
        logger = get_logger("error_handler")
        logger.warning(f"Bad request: {error}")
        return flask.jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Invalid request data",
                "status_code": 400
            }
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        logger = get_logger("error_handler")
        logger.info(f"Not found: {error}")
        return flask.jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found",
                "status_code": 404
            }
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger = get_logger("error_handler")
        logger.error(f"Internal server error: {error}", exc_info=True)
        return flask.jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "status_code": 500
            }
        }), 500

    # Log app startup
    logger = get_logger("app")
    logger.info(f"WaifuAPI starting on {config.host}:{config.port}")
    logger.info(f"Debug mode: {config.debug}")

    return app

# To run the app for development (e.g., python src/waifuapi.py)
if __name__ == '__main__':
    app = create_app()
    # Consider adding host='0.0.0.0' if you need external access
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
