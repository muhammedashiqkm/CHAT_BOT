import logging
from logging.handlers import RotatingFileHandler 
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from .config import Config

# Initialize extensions
cors = CORS()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)

    # Load configuration from the config object
    app.config.from_object(Config)

    # --- 2. Setup logging with rotation ---
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # Create a stream handler to also log to the console.
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Get the root logger, set its level, and add the handlers.
    # Note: We configure the root logger to catch logs from all libraries.
    # The original logging.basicConfig is replaced by this more detailed setup.
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    # ----------------------------------------
    
    # Initialize extensions with the app
    cors.init_app(app, origins=app.config['ALLOWED_ORIGINS'], supports_credentials=True)
    jwt.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from .routes import api_bp
    app.register_blueprint(api_bp)

    # Register error handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        # Use the configured logger
        app_logger = logging.getLogger(__name__)
        app_logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

    @app.before_request
    def log_request_info():
        # This function will now work correctly
        app_logger = logging.getLogger(__name__)
        app_logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")


    app_logger = logging.getLogger(__name__)
    app_logger.info("Application setup complete.")
    return app
    
