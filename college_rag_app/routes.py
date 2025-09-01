import logging
from flask import Blueprint, request, jsonify
from marshmallow import ValidationError
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity

from . import limiter
from .schemas import LoginSchema, SessionSchema, QuestionSchema
from .services import run_agent_async, get_session_service
from .config import Config
from .exceptions import AgentError

logger = logging.getLogger(__name__)
api_bp = Blueprint('api', __name__)
session_service = get_session_service()

@api_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
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
async def start_session():
    current_user = get_jwt_identity()
    try:
        data = SessionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]

        if username != current_user:
            return jsonify({"error": "Forbidden"}), 403

        try:
            # OPTIMIZATION NOTE: This `str(e)` check is brittle.
            # It's better to catch the specific exception for "not found"
            # from the google-adk library if one is available.
            existing_session = await session_service.get_session( 
                app_name=Config.APP_NAME, user_id=username, session_id=session_name
            )
            if existing_session:
                return jsonify({"message": "Session already exists"}), 200
        except Exception as e:
            if "Session not found" not in str(e): raise e

        await session_service.create_session(
            app_name=Config.APP_NAME, user_id=username, session_id=session_name
        )
        logger.info(f"Session '{session_name}' created for user '{username}'.")
        return jsonify({"message": "Session created"}), 201

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"Session start error: {e}")
        return jsonify({"error": "An error occurred"}), 500

@api_bp.route("/ask", methods=["POST"])
@jwt_required()
async def ask():
    current_user = get_jwt_identity()
    try:
        data = QuestionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]
        model_choice = data.get("model") or "gemini"
        
        if username != current_user:
            logger.warning(f"User '{current_user}' attempted to access session for user '{username}'.")
            return jsonify({"error": "Forbidden"}), 403
        
        try:
            await session_service.get_session(
                app_name=Config.APP_NAME,
                user_id=username,
                session_id=session_name
            )
        except Exception as e:
            if "Session not found" in str(e):
                logger.warning(f"Attempt to use non-existent session: user '{username}', session '{session_name}'.")
                return jsonify({"error": f"Session '{session_name}' not found."}), 404
            raise e

        logger.info(f"User '{username}' asking question in session '{session_name}' using model '{model_choice}'.")
        
        response_text = await run_agent_async(
            username, session_name, data["question"], model=model_choice
        )
        
        return jsonify({"response": response_text})

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except AgentError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        logger.error(f"Ask endpoint error: {e}")
        return jsonify({"error": "An internal server error occurred"}), 500

@api_bp.route("/end_session", methods=["POST"])
@jwt_required()
async def end_session():
    current_user = get_jwt_identity()
    try:
        data = SessionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]

        if username != current_user:
            return jsonify({"error": "Forbidden"}), 403

        await session_service.delete_session( 
            app_name=Config.APP_NAME, user_id=username, session_id=session_name
        )
        logger.info(f"Session '{session_name}' deleted for user '{username}'.")
        return jsonify({"message": "Session deleted"}), 200

    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        logger.error(f"End session error: {e}")
        return jsonify({"error": "An error occurred"}), 500