

### README.md

# College RAG Application

This is a Retrieval-Augmented Generation (RAG) application designed to act as a helpful AI assistant for a college. It uses Google's Generative AI and Vertex AI to answer questions related to college admissions and academic information based on a provided knowledge base.

## Project Overview

The application is a Flask-based web service that provides a set of API endpoints for user authentication, managing conversational sessions, and interacting with various AI agents. The core of the application is an AI agent that leverages a RAG corpus on Google's Vertex AI to provide accurate and context-aware answers.

## Features

  * **Multi-Model Support**: Interact with AI models from Google (Gemini), OpenAI, Anthropic, and DeepSeek.
  * **Retrieval-Augmented Generation (RAG)**: Utilizes Vertex AI RAG to pull information from a specific corpus of documents.
  * **Secure Authentication**: Employs JWT for securing API endpoints.
  * **Session Management**: Supports creating, managing, and ending user chat sessions to maintain conversational context.
  * **Rate Limiting**: Protects the login endpoint against brute-force attacks.
  * **Dockerized**: Includes a `Dockerfile` and `docker-compose.yml` for easy containerization and deployment.
  * **Asynchronous**: Built with a fully asynchronous architecture using an ASGI server (Hypercorn) for high performance.
  * **Robust Error Handling**: Gracefully handles external LLM service failures with a `503 Service Unavailable` status.

## API Documentation

All requests and responses use the JSON format. A successful request will usually return a `200 OK` or `201 Created` status code, while errors are indicated by `4xx` or `5xx` status codes.

-----

### Health Check

A simple endpoint to verify that the application is running.

  * **Endpoint**: `GET /health`
  * **Authentication**: None
  * **Success Response (`200 OK`)**:
    ```json
    {
      "status": "ok"
    }
    ```

-----

### Login

Authenticates a user and returns a JWT access token.

  * **Endpoint**: `POST /login`
  * **Authentication**: None
  * **Request Body**:
    ```json
    {
      "username": "admin",
      "password": "secure-password-here"
    }
    ```
  * **Responses**:
      * **`200 OK` (Success)**:
        ```json
        {
          "access_token": "your-jwt-access-token"
        }
        ```
      * **`400 Bad Request` (Invalid Input)**:
        ```json
        {
          "error": {
            "username": [
              "Missing data for required field."
            ]
          }
        }
        ```
      * **`401 Unauthorized` (Invalid Credentials)**:
        ```json
        {
          "error": "Invalid username or password"
        }
        ```

-----

### Start Session

Initializes a new chat session for an authenticated user.

  * **Endpoint**: `POST /start_session`
  * **Authentication**: JWT Bearer Token
  * **Request Body**:
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat"
    }
    ```
  * **Responses**:
      * **`201 Created` (New Session Created)**:
        ```json
        {
          "message": "Session created"
        }
        ```
      * **`200 OK` (Session Already Exists)**:
        ```json
        {
          "message": "Session already exists"
        }
        ```
      * **`403 Forbidden` (User Mismatch)**:
        ```json
        {
          "error": "Forbidden"
        }
        ```

-----

### Ask a Question

Submits a question to the AI agent within a specific session.

  * **Endpoint**: `POST /ask`
  * **Authentication**: JWT Bearer Token
  * **Request Body**:
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat",
      "question": "What are the admission requirements?",
      "model": "gemini"
    }
    ```
    *Note: The `model` field is optional and defaults to "gemini". Supported models: `gemini`, `openai`, `deepseek`.*
  * **Responses**:
      * **`200 OK` (Success)**:
        ```json
        {
          "response": "The admission requirements for the computer science program are..."
        }
        ```
      * **`400 Bad Request` (Invalid Model)**:
        ```json
        {
          "error": {
            "model": [
              "Must be one of: gemini, deepseek, openai, anthropic."
            ]
          }
        }
        ```
      * **`403 Forbidden` (User Mismatch)**:
        ```json
        {
          "error": "Forbidden"
        }
        ```
      * **`404 Not Found` (Session Not Found)**:
        ```json
        {
          "error": "Session 'my-first-chat' not found."
        }
        ```
      * **`503 Service Unavailable` (LLM Provider Error)**:
        ```json
        {
          "error": "The selected AI model (gemini) is currently unavailable or failed to process the request."
        }
        ```

-----

### End Session

Deletes a user's chat session and its history.

  * **Endpoint**: `POST /end_session`
  * **Authentication**: JWT Bearer Token
  * **Request Body**:
    ```json
    {
      "username": "admin",
      "session_name": "my-first-chat"
    }
    ```
  * **Responses**:
      * **`200 OK` (Success)**:
        ```json
        {
          "message": "Session deleted"
        }
        ```
      * **`403 Forbidden` (User Mismatch)**:
        ```json
        {
          "error": "Forbidden"
        }
        ```

-----

## Deployment

You can deploy this application using Docker and Docker Compose.

### Using Docker Compose (Recommended)

This is the easiest method, as it runs the application and its `memcached` dependency with a single command.

1.  **Create `.env` file**: Copy the `.env.example` file to a new file named `.env` and fill in your actual credentials and configuration details.

    ```bash
    cp .env.example .env
    ```

2.  **Build and run the services**:

    ```bash
    docker-compose up --build
    ```

    This command will build the Docker image for the API, pull the Memcached image, and start both containers. The API will be accessible at `http://localhost:5000`.

3.  **To stop the services**:

    ```bash
    docker-compose down
    ```