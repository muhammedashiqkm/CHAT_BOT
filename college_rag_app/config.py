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
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(16))
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', secrets.token_hex(32))

    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # CORS Settings
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise ValueError("FATAL: DATABASE_URL environment variable is not set.")

    # Application constants
    APP_NAME = "college_rag_app"

    # User credentials for demo
    DEMO_USER = os.getenv('DEMO_USER', 'admin')
    DEMO_PASSWORD = os.getenv('DEMO_PASSWORD', 'password')