### README.md

# College RAG Application

This is a Retrieval-Augmented Generation (RAG) application designed to act as a helpful AI assistant for a college. It uses Google's Generative AI and Vertex AI to answer questions related to college admissions and academic information based on a provided knowledge base.

## Project Overview

The application is a Flask-based web service that provides a set of API endpoints for user authentication, managing conversational sessions, and interacting with the AI agent. The core of the application is an AI agent that leverages a RAG corpus on Google's Vertex AI to provide accurate and context-aware answers.

## Features

  * **Conversational AI:** An AI assistant specialized in college-related queries.
  * **Retrieval-Augmented Generation (RAG):** Utilizes Vertex AI RAG to pull information from a specific corpus of documents.
  * **Secure Authentication:** Employs JWT for securing API endpoints.
  * **Session Management:** Supports creating, managing, and ending user chat sessions to maintain conversational context.
  * [cite\_start]**Rate Limiting:** Protects the login endpoint against brute-force attacks. [cite: 8]
  * [cite\_start]**Dockerized:** Includes a `Dockerfile` for easy containerization and deployment. [cite: 4]
  * **Asynchronous Agent:** The main AI agent logic is executed asynchronously for improved performance.

## Architecture

The application is structured as a Python Flask project:

  * `run.py`: The entry point for starting the application.
  * `college_rag_app/`: The main application package.
      * `__init__.py`: The application factory, responsible for creating and configuring the Flask app and its extensions (CORS, JWT, Limiter).
      * [cite\_start]`routes.py`: Defines all the API endpoints. [cite: 8]
      * `services.py`: Contains the core business logic, including the asynchronous agent runner.
      * `agent.py`: Defines the AI agent and its tools, including the Vertex AI RAG retrieval tool.
      * `prompts.py`: Stores the instructional prompts for the AI agent.
      * `schemas.py`: Contains Marshmallow schemas for request data validation.
      * `config.py`: Manages application configuration from environment variables.
  * `requirements.txt`: A list of all the Python dependencies.
  * [cite\_start]`Dockerfile`: A script for building the Docker image of the application. [cite: 4]
  * [cite\_start]`.env.example`: An example file for the necessary environment variables. [cite: 1]

## Prerequisites

  * [cite\_start]Python 3.11 [cite: 4]
  * Docker
  * A Google Cloud Platform project with Vertex AI enabled.
  * A RAG corpus created in Vertex AI.

## Installation

1.  **Clone the repository:**

    ```bash
    git clone <your-repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a Python virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**

      * Create a `.env` file by copying the example file:
        ```bash
        cp .env.example .env
        ```
      * [cite\_start]Modify the `.env` file with your specific configurations for Google Cloud, security keys, and the database URL. [cite: 1]

## Running the Application

### Development

To run the application in development mode with the Flask server:

```bash
export FLASK_APP=run.py
export FLASK_DEBUG=True
flask run
```

### Production

For production, it is recommended to use a WSGI server like Gunicorn. [cite\_start]The provided `Dockerfile` is configured to use Gunicorn. [cite: 8]

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 "college_rag_app:create_app()"
```

## API Documentation

### Health Check

  * **Endpoint:** `GET /health`
  * **Description:** A health check endpoint to verify that the application is running.
  * **Authentication:** None
  * **Success Response (200 OK):**
    ```json
    {
      "status": "ok"
    }
    ```

### Login

  * **Endpoint:** `POST /login`
  * [cite\_start]**Description:** Authenticates a user and returns a JWT access token. [cite: 8]
  * **Authentication:** None
  * **Request Body:**
    ```json
    {
      "username": "admin",
      "password": "secure-password-here"
    }
    ```
  * **Success Response (200 OK):**
    ```json
    {
      "access_token": "your-jwt-access-token"
    }
    ```
  * **Error Response (401 Unauthorized):**
    ```json
    {
      "error": "Invalid username or password"
    }
    ```

### Start Session

  * **Endpoint:** `POST /start_session`
  * **Description:** Initializes a new chat session for a user.
  * **Authentication:** JWT Bearer Token required.
  * **Request Body:**
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat"
    }
    ```
  * **Success Response (201 Created):**
    ```json
    {
      "message": "Session created"
    }
    ```
  * **Error Response (403 Forbidden):**
    ```json
    {
      "error": "Forbidden"
    }
    ```

### Ask a Question

  * **Endpoint:** `POST /ask`
  * **Description:** Submits a question to the AI agent within a specific session.
  * **Authentication:** JWT Bearer Token required.
  * **Request Body:**
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat",
      "question": "What are the admission requirements for the computer science program?"
    }
    ```
  * **Success Response (200 OK):**
    ```json
    {
      "response": "The admission requirements for the computer science program are..."
    }
    ```
  * **Error Response (404 Not Found):**
    ```json
    {
      "error": "Session 'my-first-chat' not found."
    }
    ```

### End Session

  * **Endpoint:** `POST /end_session`
  * **Description:** Deletes a user's chat session.
  * **Authentication:** JWT Bearer Token required.
  * **Request Body:**
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat"
    }
    ```
  * **Success Response (200 OK):**
    ```json
    {
      "message": "Session deleted"
    }
    ```
  * **Error Response (403 Forbidden):**
    ```json
    {
      "error": "Forbidden"
    }
    ```

## Environment Variables

[cite\_start]The application's configuration is managed through environment variables. [cite: 1]

  * [cite\_start]`GOOGLE_GENAI_USE_VERTEXAI`: Set to `1` to use Vertex AI. [cite: 1]
  * [cite\_start]`GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID. [cite: 1]
  * [cite\_start]`GOOGLE_CLOUD_LOCATION`: The Google Cloud location (e.g., `us-central1`). [cite: 1]
  * [cite\_start]`RAG_CORPUS`: The full resource name of your RAG corpus in Vertex AI. [cite: 1]
  * [cite\_start]`GOOGLE_APPLICATION_CREDENTIALS`: The path to your Google Cloud service account key file. [cite: 1]
  * `GENAI_MODEL_NAME`: The name of the generative model to use (e.g., `gemini-1.0-pro-001`).
  * [cite\_start]`SECRET_KEY`: A secret key for Flask application security. [cite: 1]
  * [cite\_start]`JWT_SECRET_KEY`: A secret key for JWT token generation. [cite: 1]
  * [cite\_start]`DEMO_USER`: The username for the demo user. [cite: 1]
  * [cite\_start]`DEMO_PASSWORD`: The password for the demo user. [cite: 1]
  * [cite\_start]`ALLOWED_ORIGINS`: A comma-separated list of allowed origins for CORS. [cite: 1]
  * [cite\_start]`FLASK_DEBUG`: Set to `True` for development to enable debug mode. [cite: 1]
  * [cite\_start]`DATABASE_URL`: The connection string for the PostgreSQL database. [cite: 1]
  * `RATELIMIT_STORAGE_URI`: The URI for the rate limiting storage (e.g., `memcached://localhost:11211`).

## Docker Deployment

The application can be built and run as a Docker container using the provided `Dockerfile`.

1.  **Build the Docker image:**

    ```bash
    docker build -t college-rag-app .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -p 5000:5000 -v /path/to/your/gcloud/credentials:/path/in/container \
           -e GOOGLE_APPLICATION_CREDENTIALS="/path/in/container/your-service-account-key.json" \
           -e SECRET_KEY="your-secret-key" \
           -e JWT_SECRET_KEY="your-jwt-secret-key" \
           -e DEMO_USER="admin" \
           -e DEMO_PASSWORD="your-secure-password" \
           -e DATABASE_URL="your-database-url" \
           -e GOOGLE_CLOUD_PROJECT="your-gcp-project-id" \
           -e GOOGLE_CLOUD_LOCATION="us-central1" \
           -e RAG_CORPUS="your-rag-corpus-id" \
           -e GENAI_MODEL_NAME="gemini-1.0-pro-001" \
           college-rag-app
    ```

    Make sure to replace the placeholder values with your actual configuration. The `-v` flag is used to mount the Google Cloud credentials file into the container.

[cite\_start]The `Dockerfile` also includes a `HEALTHCHECK` instruction to ensure the container is running correctly. [cite: 4]

## Contributing

Contributions are welcome\! Please feel free to submit a pull request or open an issue for any bugs or feature requests.
