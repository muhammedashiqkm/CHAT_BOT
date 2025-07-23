import asyncio
import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

from . import limiter
from .schemas import LoginSchema, SessionSchema, QuestionSchema
from .services import run_agent_async, get_session_service
from .config import Config

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)
session_service = get_session_service()

@api_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint for Docker.
    Responds with a simple 'ok' status if the app is running.
    """
    return jsonify({"status": "ok"}), 200

@api_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    try:
        data = LoginSchema().load(request.json)
        username = data["username"]
        password = data["password"]

        if username == Config.DEMO_USER and password == Config.DEMO_PASSWORD:
            access_token = create_access_token(identity=username)
            logger.info(f"User '{username}' logged in successfully.")
            return jsonify(access_token=access_token), 200
        else:
            logger.warning(f"Failed login attempt for user '{username}'.")
            return jsonify({"error": "Invalid username or password"}), 401
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({"error": "An error occurred during authentication"}), 500

@api_bp.route("/start_session", methods=["POST"])
@jwt_required()
def start_session():
    current_user = get_jwt_identity()
    try:
        data = SessionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]

        if username != current_user:
            return jsonify({"error": "Forbidden"}), 403

        try:
            existing_session = asyncio.run(session_service.get_session(
                app_name=Config.APP_NAME, user_id=username, session_id=session_name
            ))
            if existing_session:
                return jsonify({"message": "Session already exists"}), 200
        except Exception as e:
            if "Session not found" not in str(e): raise e

        asyncio.run(session_service.create_session(
            app_name=Config.APP_NAME, user_id=username, session_id=session_name
        ))
        logger.info(f"Session '{session_name}' created for user '{username}'.")
        return jsonify({"message": f"Session created"}), 201

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"Session start error: {e}")
        return jsonify({"error": "An error occurred"}), 500

@api_bp.route("/ask", methods=["POST"])
@jwt_required()
def ask():
    current_user = get_jwt_identity()
    try:
        data = QuestionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]
        
        if username != current_user:
            logger.warning(f"User '{current_user}' attempted to access session for user '{username}'.")
            return jsonify({"error": "Forbidden"}), 403
        
        # --- NEW: Check if session exists before asking a question ---
        try:
            asyncio.run(session_service.get_session(
                app_name=Config.APP_NAME,
                user_id=username,
                session_id=session_name
            ))
        except Exception as e:
            if "Session not found" in str(e):
                logger.warning(f"Attempt to use non-existent session: user '{username}', session '{session_name}'.")
                return jsonify({"error": f"Session '{session_name}' not found."}), 404
            # For other errors, let the main handler catch it
            raise e
        # ----------------------------------------------------------------

        logger.info(f"User '{username}' asking question in session '{session_name}'.")
        response_text = asyncio.run(run_agent_async(
            username, session_name, data["question"]
        ))
        
        return jsonify({"response": response_text})

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"Ask endpoint error: {e}")
        return jsonify({"error": "An error occurred"}), 500

@api_bp.route("/end_session", methods=["POST"])
@jwt_required()
def end_session():
    current_user = get_jwt_identity()
    try:
        data = SessionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]

        if username != current_user:
            return jsonify({"error": "Forbidden"}), 403

        asyncio.run(session_service.delete_session(
            app_name=Config.APP_NAME, user_id=username, session_id=session_name
        ))
        logger.info(f"Session '{session_name}' deleted for user '{username}'.")
        return jsonify({"message": "Session deleted"}), 200

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"End session error: {e}")
        return jsonify({"error": "An error occurred"}), 500