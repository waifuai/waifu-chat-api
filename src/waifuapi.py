import os
import flask
from dotenv import load_dotenv

# Import blueprints
from .blueprints.users import users_bp
from .blueprints.dialog import dialog_bp
from .blueprints.status import status_bp
from .blueprints.chat import chat_bp

def create_app(config_override=None):
    """Creates and configures the Flask application."""
    app = flask.Flask(__name__)

    # Load environment variables from .env file first
    load_dotenv()

    # Default configuration
    app.config.from_mapping(
        DATABASE_FILE=os.environ.get('DATABASE_FILE', 'dialogs.db'),
        # Add other default config values if needed
    )

    # Override config with provided dictionary (for testing)
    if config_override:
        app.config.from_mapping(config_override)

    # Ensure the instance folder exists (if needed, though not used here yet)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints
    app.register_blueprint(users_bp, url_prefix='/v1/user')
    app.register_blueprint(dialog_bp, url_prefix='/v1/user/dialog')
    app.register_blueprint(status_bp, url_prefix='/v1/server')
    app.register_blueprint(chat_bp)

    # Register database cleanup function
    from . import waifuapi_db
    app.teardown_appcontext(waifuapi_db.close_db)

    # You could initialize database connections or other extensions here
    # using the app context if needed, e.g., app.cli.add_command(init_db_command)

    return app

# To run the app for development (e.g., python src/waifuapi.py)
if __name__ == '__main__':
    app = create_app()
    # Consider adding host='0.0.0.0' if you need external access
    app.run(debug=True, port=int(os.environ.get('PORT', 5000)))
