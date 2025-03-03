from dotenv import load_dotenv
load_dotenv()

import flask
from .blueprints.users import users_bp
from .blueprints.dialog import dialog_bp
from .blueprints.status import status_bp
from .blueprints.chat import chat_bp

app = flask.Flask(__name__)

app.register_blueprint(users_bp, url_prefix='/v1/user')
app.register_blueprint(dialog_bp, url_prefix='/v1/user/dialog')
app.register_blueprint(status_bp, url_prefix='/v1/server')
app.register_blueprint(chat_bp)
