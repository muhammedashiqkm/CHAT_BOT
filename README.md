
# College RAG App API

This document details the API endpoints for the RAG (Retrieval-Augmented Generation) chatbot application.

**Note**: All endpoints, except `/login` and `/health`, are protected. They require an `Authorization: Bearer <your_access_token>` header obtained from the login route. Admin routes require a token generated for an admin user.

-----

## Health & Authentication

### `GET /health`

Checks the health of the API server.

  * **Auth**: None.
  * **Success Response (200 OK)**:
    ```json
    {
      "status": "ok"
    }
    ```

### `POST /login`

Authenticates a user and returns a JSON Web Token (JWT). The credentials for the demo admin user are set via `DEMO_USER` and `DEMO_PASSWORD` environment variables.

  * **Auth**: None.
  * **Request Body**:
    ```json
    {
      "username": "your_demo_user",
      "password": "your_demo_password"
    }
    ```
  * **Success Response (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

-----

## User Session & Chat

### `POST /start_session`

Initializes a new chat session history for a user.

  * **Auth**: JWT Required.
  * **Request Body**:
    ```json
    {
      "username": "your_demo_user",
      "session_name": "my-first-session"
    }
    ```
  * **Success Response (201 Created)**:
    ```json
    {
      "message": "Session created"
    }
    ```

### `POST /ask`

Submits a question to the RAG agent within a specific session. Requires a valid model choice.

  * **Auth**: JWT Required.

  * **Request Body**:

    ```json
    {
      "username": "your_demo_user",
      "session_name": "my-first-session",
      "question": "What are the admission requirements?",
      "model": "gemini"
    }
    ```

      * **`model`** (required): Must be one of the configured agent models. Your code supports `"gemini"`, `"openai"`, and `"deepseek"`.

  * **Success Response (200 OK)**:

    ```json
    {
      "response": "<p>Here are the admission requirements...</p><ul><li>Requirement 1</li></ul>"
    }
    ```

### `POST /end_session`

Deletes a user's chat session history from the database.

  * **Auth**: JWT Required.
  * **Request Body**:
    ```json
    {
      "username": "your_demo_user",
      "session_name": "my-first-session"
    }
    ```
  * **Success Response (200 OK)**:
    ```json
    {
      "message": "Session deleted"
    }
    ```

-----

## Admin: Document Management

These endpoints are used to manage the RAG knowledge base. They require an **Admin** JWT.

### `GET /document_details`

Lists all ingested documents and their current processing status.

  * **Auth**: JWT Required (any authenticated user).
  * **Success Response (200 OK)**:
    ```json
    [
      {
        "id": "a1b2c3d4-...",
        "display_name": "Undergraduate Catalog 2025",
        "source_url": "https://.../catalog.pdf",
        "status": "COMPLETED",
        "error": null,
        "created_at": "2025-09-01T10:30:00+00:00"
      }
    ]
    ```

### `POST /document`

Submits a new document (from a public URL) for ingestion. This triggers the background process of fetching, chunking, embedding, and saving the document.

  * **Auth**: Admin JWT Required.
  * **Request Body**:
    ```json
    {
      "source_url": "https://example.com/path/to/document.pdf",
      "display_name": "Example Document Name"
    }
    ```
  * **Success Response (201 Created)**:
    ```json
    {
      "message": "Document ingestion started.",
      "status": "PENDING",
      "document_id": "e5f6a7b8-..."
    }
    ```

### `GET /document/<doc_id>`

Retrieves the status and details for a single document, including its chunk count.

  * **Auth**: JWT Required (any authenticated user).
  * **Success Response (200 OK)**:
    ```json
    {
        "id": "a1b2c3d4-...",
        "display_name": "Undergraduate Catalog 2025",
        "source_url": "https://.../catalog.pdf",
        "status": "COMPLETED",
        "error": null,
        "created_at": "2025-09-01T10:30:00+00:00",
        "chunk_count": 150
    }
    ```

### `DELETE /document/<doc_id>`

Deletes a document and all its associated vector chunks from the database.

  * **Auth**: Admin JWT Required.
  * **Success Response (200 OK)**:
    ```json
    {
      "message": "Document 'Undergraduate Catalog 2025' deleted."
    }
    ```

### `POST /document/<doc_id>/re_ingest`

Deletes all old chunks for a document and triggers a fresh ingestion process using the document's existing `source_url`.

  * **Auth**: Admin JWT Required.
  * **Success Response (200 OK)**:
    ```json
    {
      "message": "Document re-ingestion started.",
      "status": "PENDING_REINGEST",
      "document_id": "a1b2c3d4-..."
    }
    ```