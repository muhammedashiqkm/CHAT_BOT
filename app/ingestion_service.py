import requests
import io
import fitz 
import logging
import time
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from flask import current_app

from .config import Config
from .exceptions import ExternalApiError
from .models import db, Document, DocumentChunk


error_logger = logging.getLogger('error')
app_logger = logging.getLogger('app')



def get_pdf_text(pdf_url: str) -> str | None:
    """Downloads a PDF from a URL and extracts its text content using PyMuPDF."""
    try:
        response = requests.get(pdf_url, timeout=30)
        response.raise_for_status() 
        pdf_file = io.BytesIO(response.content)
        
        text = ""
        with fitz.open(stream=pdf_file, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
        
        repaired_text = text.encode('utf-16', 'surrogatepass').decode('utf-16')
        clean_text = repaired_text.replace('\x00', '')
        
        return clean_text
    except requests.exceptions.RequestException as e:
        error_logger.error(f"Error downloading PDF from {pdf_url}: {e}")
        return None
    except Exception as e:
        error_logger.error(f"Error processing PDF from {pdf_url}: {e}")
        return None


def get_text_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    """Splits a long text into smaller, manageable chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks



def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    try:
        model_name = current_app.config.get("EMBEDDING_MODEL_NAME")
        result = genai.embed_content(
            model=model_name,
            content=texts,
            task_type="retrieval_document",
            output_dimensionality=current_app.config.get("PG_EMBEDDING_DIMENSION")
        )
        return result['embedding']
    except Exception as e:
        error_logger.error(f"Error getting batch embedding from GenAI: {e}", exc_info=True)
        raise ExternalApiError("The embedding service failed.") from e



def process_and_store_document(document: Document) -> None:
    """
    Orchestrator function: takes a Document object, processes it,
    and stores chunks in the database. Updates the document status.
    """
    start_time = time.monotonic()
    
    try:
        app_logger.info(f"Starting ingestion for doc ID: {document.id} ({document.display_name})")
        
        # 1. Get Text
        document.processing_status = "FETCHING"
        db.session.commit()
        raw_text = get_pdf_text(document.source_url)
        if not raw_text:
            raise ValueError("Failed to extract text from PDF (empty content).")

        # 2. Get Chunks
        document.processing_status = "CHUNKING"
        db.session.commit()

        
        chunk_size = current_app.config['TEXT_CHUNK_SIZE']
        chunk_overlap = current_app.config['TEXT_CHUNK_OVERLAP']
        chunks = get_text_chunks(raw_text, chunk_size, chunk_overlap)

        if not chunks:
            raise ValueError("Text was extracted but resulted in no chunks.")
        app_logger.info(f"Created {len(chunks)} chunks for doc ID: {document.id}")

        # 3. Get Embeddings (Batch)
        document.processing_status = "EMBEDDING"
        db.session.commit()
        embeddings = get_embeddings_batch(chunks)

        # 4. Create DocumentChunk objects
        document.processing_status = "SAVING"
        db.session.commit()
        chunks_to_add = []
        for content, embedding in zip(chunks, embeddings):
            chunk_obj = DocumentChunk(
                content=content,
                embedding=embedding,
                document_id=document.id
            )
            chunks_to_add.append(chunk_obj)

        # 5. Bulk-save chunks
        db.session.bulk_save_objects(chunks_to_add)
        
        # 6. Mark as complete
        end_time = time.monotonic()
        document.processing_status = "COMPLETED"
        document.processing_time_ms = int((end_time - start_time) * 1000)
        document.processing_error = None
        app_logger.info(f"Successfully completed ingestion for doc ID: {document.id}")

    except (ValueError, ExternalApiError, Exception) as e:
        error_logger.error(f"Ingestion FAILED for doc ID {document.id}: {e}", exc_info=True)
        document.processing_status = "FAILED"
        document.processing_error = str(e)
    
    finally:
        db.session.commit()