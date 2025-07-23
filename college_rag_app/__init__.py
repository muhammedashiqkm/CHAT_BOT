import logging
from flask import Flask, jsonify, request # <- FIX: Added 'request' here
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

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("app.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)

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
        logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({"error": "An internal server error occurred"}), 500

    @app.before_request
    def log_request_info():
        # This function will now work correctly
        logger.info(f"Request: {request.method} {request.path} from {request.remote_addr}")


    logger.info("Application setup complete.")
    return app