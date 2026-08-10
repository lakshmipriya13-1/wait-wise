import os

from flask import Flask, render_template
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.config import config_by_name
from app.extensions import db, migrate, login_manager, socketio


def create_app(config_name=None):
    """Application factory for WaitWise."""

    if not config_name:
        config_name = os.environ.get("FLASK_ENV", "development")

    # Create Flask application
    flask_app = Flask(
        __name__,
        template_folder="../frontend/templates",
        static_folder="../frontend/static",
    )

    # Load configuration
    flask_app.config.from_object(config_by_name[config_name])

    # ---------------------------------------------------------
    # Initialize Flask extensions
    # ---------------------------------------------------------
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)

    login_manager.init_app(flask_app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # ---------------------------------------------------------
    # Initialize SocketIO
    # ---------------------------------------------------------
    message_queue = flask_app.config.get("SOCKETIO_MESSAGE_QUEUE")

    if message_queue:
        socketio.init_app(
            flask_app,
            message_queue=message_queue,
            cors_allowed_origins="*",
        )
    else:
        socketio.init_app(
            flask_app,
            cors_allowed_origins="*",
        )

    # ---------------------------------------------------------
    # Flask-Login user loader
    # ---------------------------------------------------------
    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ---------------------------------------------------------
    # Register blueprints
    # ---------------------------------------------------------
    from app.routes import main_bp
    from app.routes.auth import auth_bp
    from app.routes.user import user_bp
    from app.routes.queue import queue_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    from app.routes.ai import ai_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(user_bp)
    flask_app.register_blueprint(queue_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(api_bp)
    flask_app.register_blueprint(ai_bp)

    # ---------------------------------------------------------
    # Register SocketIO event handlers
    # ---------------------------------------------------------
    import app.sockets.queue_socket  # noqa: F401

    # ---------------------------------------------------------
    # Error handlers
    # ---------------------------------------------------------
    @flask_app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(500)
    def internal_server_error(error):
        from app.utils.logger import logger

        logger.error(
            f"Internal Server Error: {str(error)}",
            exc_info=True,
        )

        return render_template("errors/500.html"), 500

    return flask_app
