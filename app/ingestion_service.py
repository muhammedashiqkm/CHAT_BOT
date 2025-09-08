from flask import Blueprint, request, jsonify, current_app
from marshmallow import ValidationError
from flask_jwt_extended import (
    jwt_required, create_access_token, get_jwt_identity, get_jwt
)
import logging
import uuid
import threading
import os
from functools import wraps 

from . import limiter
from .schemas import LoginSchema, SessionSchema, QuestionSchema
from .services import run_agent_async, get_session_service
from .exceptions import AgentError
from .config import Config 

from .models import db, Document, DocumentChunk

# Get the loggers
app_logger = logging.getLogger('app')
security_logger = logging.getLogger('security')
error_logger = logging.getLogger('error')

api_bp = Blueprint('api', __name__)
session_service = get_session_service()

UPLOAD_FOLDER = '/app/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def admin_required(fn):
    """Custom decorator to require admin claims in JWT."""
    @wraps(fn)
    @jwt_required() 
    def wrapper(*args, **kwargs):
        claims = get_jwt()
        if not claims.get("is_admin"):
            security_logger.warning(
                f"Non-admin user '{get_jwt_identity()}' attempted admin operation."
            )
            return jsonify({"error": "Administration access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


@api_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok"}), 200

@api_bp.route("/login", methods=["POST"])
@limiter.limit("10 per minute")
def login():
    try:
        data = LoginSchema().load(request.json)
        username = data["username"]
        password = data["password"]

        if username == Config.DEMO_USER and password == Config.DEMO_PASSWORD:
            additional_claims = {"is_admin": True}
            access_token = create_access_token(
                identity=username, 
                additional_claims=additional_claims
            )
            security_logger.info(f"User '{username}' logged in successfully (Demo Admin).")
            return jsonify(access_token=access_token), 200
        else:
            security_logger.warning(f"Failed login attempt for user '{username}'.")
            return jsonify({"error": "Invalid username or password"}), 401
            
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        error_logger.error(f"Login error: {e}", exc_info=True)
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
        return jsonify({"message": "Session created"}), 201
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        error_logger.error(f"Session start error: {e}", exc_info=True)
        return jsonify({"error": "An error occurred"}), 500

@api_bp.route("/ask", methods=["POST"])
@jwt_required()
async def ask():
    current_user = get_jwt_identity() 
    model_choice = ""
    try:
        data = QuestionSchema().load(request.json)
        username = data["username"]
        session_name = data["session_name"]
        model_choice = data["model"] 
        
        if username != current_user:
            return jsonify({"error": "Forbidden"}), 403
        
        try:
            session = await session_service.get_session(
                app_name=current_app.config['APP_NAME'],
                user_id=username,
                session_id=session_name
            )
            if not session:
                return jsonify({"error": f"Session '{session_name}' not found."}), 404
        except Exception as e:
            error_logger.error(f"Error during get_session for user '{username}': {e}", exc_info=True)
            return jsonify({"error": "An error occurred while retrieving the session."}), 500
        
        response_text = await run_agent_async(
            username, session_name, data["question"], model=model_choice
        )
        return jsonify({"response": response_text})
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except AgentError as e:
        return jsonify({"error": str(e)}), 503
    except Exception as e:
        error_logger.error(f"Ask endpoint error: {e}", exc_info=True)
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
        return jsonify({"message": "Session deleted"}), 200
    except ValidationError as err:
        return jsonify({"error": err.messages}), 400
    except Exception as e:
        error_logger.error(f"End session error: {e}", exc_info=True)
        return jsonify({"error": "An error occurred"}), 500


def run_ingestion_in_background(app, doc_id):
    """
    Runs the blocking ingestion process in a new thread with its own app context
    to avoid blocking the main ASGI server.
    (This function remains unchanged, its logic is still perfect)
    """
    with app.app_context():
        try:
            doc = Document.query.get(doc_id)
            if not doc:
                error_logger.error(f"[BG_JOB] Failed to find Document {doc_id} to start ingestion.")
                return

            process_and_store_document(doc) 

        except Exception as e:
            error_logger.error(f"[BG_JOB] Ingestion failed for {doc_id}: {e}", exc_info=True)
            try:
                db.session.rollback() 
                doc_to_fail = Document.query.get(doc_id)
                if doc_to_fail:
                    doc_to_fail.processing_status = "FAILED"
                    doc_to_fail.processing_error = f"Background task error: {str(e)}"
                    db.session.commit()
            except Exception as db_e:
                error_logger.error(f"[BG_JOB] FATAL: Failed to even update error status for {doc_id}: {db_e}")


@api_bp.route("/document", methods=["POST"])
@admin_required
def create_document():
    """
    Creates a new Document record and triggers ingestion IN THE BACKGROUND.
    This endpoint accepts multipart/form-data with either:
    1. A file upload: { "display_name": "...", "file": <PDF_FILE> }
    2. A URL (G-Drive or Direct): { "display_name": "...", "source_url": "..." }
    """
    try:
        display_name = request.form.get("display_name")
        if not display_name:
            return jsonify({"error": "Missing required field: display_name"}), 400

        source_url_from_form = request.form.get("source_url")
        uploaded_file = request.files.get("file")

        if not uploaded_file and not source_url_from_form:
            return jsonify({"error": "Must provide either a 'file' upload or a 'source_url' field"}), 400
        
        new_doc = Document(
            display_name=display_name,
            processing_status="PENDING" 
        )
        
        if uploaded_file:
            if uploaded_file.filename == '':
                return jsonify({"error": "File field provided but no file was selected"}), 400
            
            # Save doc to get the ID
            db.session.add(new_doc)
            db.session.commit()
            
            # Save file locally using its new UUID, guaranteeing a unique filename
            # Note: We just use the file extension from the original upload for clarity
            _, file_ext = os.path.splitext(uploaded_file.filename)
            if not file_ext:
                file_ext = ".pdf" # Default to .pdf if extension is missing
                
            local_filename = f"{str(new_doc.id)}{file_ext}"
            local_filepath = os.path.join(UPLOAD_FOLDER, local_filename)
            uploaded_file.save(local_filepath)
            
            # Save the *internal file path* as the source_url for the background job
            new_doc.source_url = local_filepath
            app_logger.info(f"File uploaded and saved locally to {local_filepath}")

        else:
            # No file uploaded, use the provided source_url (G-Drive or direct link)
            new_doc.source_url = source_url_from_form
            db.session.add(new_doc)
            db.session.commit()

        # Commit the final changes (like the source_url if it was a file upload)
        db.session.commit()
        
        # The background thread logic remains the same. It just needs the doc_id.
        app = current_app._get_current_object() 
        thread = threading.Thread(
            target=run_ingestion_in_background, 
            args=(app, new_doc.id)
        )
        thread.start()
     
        return jsonify({
            "message": "Document ingestion started.", 
            "status": new_doc.processing_status,
            "document_id": new_doc.id,
            "source": new_doc.source_url
        }), 201

    except Exception as e:
        db.session.rollback()
        error_logger.error(f"Failed to create document: {e}", exc_info=True)
        if "UniqueViolation" in str(e):
             return jsonify({"error": f"A document with the name '{display_name}' already exists."}), 409
        return jsonify({"error": f"An internal error occurred: {e}"}), 500


@api_bp.route("/document_details", methods=["GET"])
@jwt_required()
def get_documents():
    """Lists all documents and their processing status."""
    try:
        documents = Document.query.all()
        results = [
            {
                "id": doc.id,
                "display_name": doc.display_name,
                "source_url": doc.source_url,
                "status": doc.processing_status,
                "error": doc.processing_error,
                "created_at": doc.created_at.isoformat(),
            } for doc in documents
        ]
        return jsonify(results)
    except Exception as e:
        error_logger.error(f"Failed to list documents: {e}", exc_info=True)
        return jsonify({"error": "Failed to retrieve documents."}), 500


@api_bp.route("/document/<doc_id>", methods=["GET"])
@jwt_required()
def get_document(doc_id):
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        return jsonify({"error": "Invalid document ID format"}), 400
        
    doc = Document.query.get_or_404(doc_uuid)
    
    return jsonify({
        "id": doc.id,
        "display_name": doc.display_name,
        "source_url": doc.source_url,
        "status": doc.processing_status,
        "error": doc.processing_error,
        "created_at": doc.created_at.isoformat(),
        "chunk_count": len(doc.chunks) 
    })

@api_bp.route("/document/<doc_id>", methods=["DELETE"])
@admin_required
def delete_document(doc_id):
    """Deletes a document and all its associated chunks."""
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        return jsonify({"error": "Invalid document ID format"}), 400
        
    doc = Document.query.get_or_404(doc_uuid)
    
    try:
        db.session.delete(doc)
        db.session.commit()
        app_logger.info(f"Admin '{get_jwt_identity()}' deleted document {doc_id} ({doc.display_name})")
        return jsonify({"message": f"Document '{doc.display_name}' deleted."}), 200
    except Exception as e:
        db.session.rollback()
        error_logger.error(f"Failed to delete document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to delete document."}), 500


@api_bp.route("/document/<doc_id>/re_ingest", methods=["POST"])
@admin_required
def re_ingest_document(doc_id):
    """
    Re-processes a document. This deletes all old chunks and re-runs
    the full ingestion pipeline IN THE BACKGROUND.
    (This function remains unchanged, its logic is still perfect)
    """
    try:
        doc_uuid = uuid.UUID(doc_id)
    except ValueError:
        return jsonify({"error": "Invalid document ID format"}), 400
        
    doc = Document.query.get_or_404(doc_uuid)
    
    try:
        DocumentChunk.query.filter_by(document_id=doc.id).delete()
        
        doc.processing_status = "PENDING_REINGEST"
        doc.processing_error = None
        db.session.commit()
        
        app = current_app._get_current_object() 
        thread = threading.Thread(
            target=run_ingestion_in_background, 
            args=(app, doc.id)
        )
        thread.start()
        
        app_logger.info(f"Admin '{get_jwt_identity()}' triggered re-ingestion for {doc_id}")
        

        return jsonify({
            "message": "Document re-ingestion started.",
            "status": doc.processing_status,
            "document_id": doc.id
        }), 200

    except Exception as e:
        db.session.rollback()
        error_logger.error(f"Failed to re-ingest document {doc_id}: {e}", exc_info=True)
        return jsonify({"error": "Failed to re-ingest document."}), 500