import os
import secrets
import logging
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# UPDATED: Get a logger instance
logger = logging.getLogger(__name__)

class Config:
    """
    Application configuration class.
    Loads settings from environment variables.
    """

    #Google Application Credentials
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Secret Keys
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "1")))

    # CORS Settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # In production, set this to your Memcached server's address.
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

    # Ensure critical secrets are set
    if not SECRET_KEY:
        raise ValueError("FATAL: SECRET_KEY environment variable is not set.")
    if not JWT_SECRET_KEY:
        raise ValueError("FATAL: JWT_SECRET_KEY environment variable is not set.")
    if not DEMO_USER or not DEMO_PASSWORD:
        logger.warning("DEMO_USER or DEMO_PASSWORD not set. This is okay if using another auth method.")