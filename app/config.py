# file: config.py
import os
import secrets
import logging
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    """
    Application configuration class.
    Loads settings from environment variables.
    """

    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("FATAL: GOOGLE_API_KEY environment variable is not set.")

    # Secret Keys
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "1")))

    
    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv("MEMCACHED_URL","memcached://memcached:11211")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("FATAL: DATABASE_URL environment variable is not set.")

    # Application constants
    APP_NAME = "college_rag_app"

    # User credentials for demo
    DEMO_USER = os.getenv('DEMO_USER')
    DEMO_PASSWORD = os.getenv('DEMO_PASSWORD')
    
    # These variables are required by agent.py and ingestion_service.py
    TEXT_CHUNK_SIZE = int(os.getenv("TEXT_CHUNK_SIZE", 1000))
    TEXT_CHUNK_OVERLAP = int(os.getenv("TEXT_CHUNK_OVERLAP", 200))
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "models/gemini-embedding-001")
    
    # These MUST match your models.py definitions
    PG_TABLE_NAME = os.getenv("PG_TABLE_NAME", "document_chunks") 
    PG_VECTOR_COLUMN = os.getenv("PG_VECTOR_COLUMN", "embedding") 
    PG_CONTENT_COLUMN = os.getenv("PG_CONTENT_COLUMN", "content") 
    PG_EMBEDDING_DIMENSION = int(os.getenv("PG_EMBEDDING_DIMENSION", "768"))


    if not SECRET_KEY:
        raise ValueError("FATAL: SECRET_KEY environment variable is not set.")
    if not JWT_SECRET_KEY:
        raise ValueError("FATAL: JWT_SECRET_KEY environment variable is not set.")
    if not DEMO_USER or not DEMO_PASSWORD:
        logger.warning("DEMO_USER or DEMO_PASSWORD not set. Login will fail.")