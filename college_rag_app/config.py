import os
import secrets
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    Application configuration class.
    Loads settings from environment variables.
    """

    #Google Application Credentials
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # Secret Keys
    # In production, ensure SECRET_KEY and JWT_SECRET_KEY are set securely as environment variables.
    # Do not rely on default or dynamically generated values at each app start.
    SECRET_KEY = os.getenv('SECRET_KEY')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')

    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_HOURS", "1")))

    # CORS Settings
    # IMPORTANT: In production, specify exact trusted origins instead of "*".
    # Example: ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "https://yourfrontend.com").split(",")
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
    # In production, consider removing demo credentials or using a proper user management system.
    DEMO_USER = os.getenv('DEMO_USER')
    DEMO_PASSWORD = os.getenv('DEMO_PASSWORD')

    # Ensure critical secrets are set
    if not SECRET_KEY:
        raise ValueError("FATAL: SECRET_KEY environment variable is not set.")
    if not JWT_SECRET_KEY:
        raise ValueError("FATAL: JWT_SECRET_KEY environment variable is not set.")
    if not DEMO_USER or not DEMO_PASSWORD:
        # This check can be adjusted based on whether demo user is strictly required in prod
        print("WARNING: DEMO_USER or DEMO_PASSWORD not set. This is okay if using another auth method.")
