import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import google.generativeai as genai

from .config import Config
from .models import db

def setup_logger(name, log_file, level=logging.INFO):
    """Function to set up a logger."""
    log_directory = 'logs'
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    handler = RotatingFileHandler(f'{log_directory}/{log_file}', maxBytes=10485760, backupCount=5)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s [in %(pathname)s:%(lineno)d]',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(stream_handler)
    logger.propagate = False
    return logger

app_logger = setup_logger('app', 'app.log')
error_logger = setup_logger('error', 'error.log', logging.ERROR)
access_logger = setup_logger('access', 'access.log')
security_logger = setup_logger('security', 'security.log')


cors = CORS()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)

def create_app():
    """
    Application factory function to create and configure the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(Config)
    
    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        app_logger.info("Google AI SDK configured successfully.")
    except Exception as e:
        app_logger.critical(f"FATAL: Failed to configure Google AI SDK: {e}", exc_info=True)
        error_logger.critical(f"FATAL: Failed to configure Google AI SDK: {e}", exc_info=True)


    
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)

    cors.init_app(app, origins=app.config['ALLOWED_ORIGINS'], supports_credentials=True)
    jwt.init_app(app)
    limiter.init_app(app)

    from .routes import api_bp
    app.register_blueprint(api_bp)

    with app.app_context():
        try:
            db.create_all()
            app_logger.info("Database tables created or already exist.")
        except Exception as e:
            app_logger.critical(f"FATAL: Database table creation failed: {e}", exc_info=True)
            error_logger.critical(f"Database creation error. Did you remember to run 'CREATE EXTENSION IF NOT EXISTS vector;' in PostgreSQL?", exc_info=True)


    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(e):
        return jsonify({"error": "Method not allowed"}), 405
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        error_logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500

    @app.before_request
    def log_request_info():
        access_logger.info(
            f"{request.method} {request.path} from {request.remote_addr} - Agent: {request.headers.get('User-Agent')}"
        )

    app_logger.info("Application setup complete.")
    return app