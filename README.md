Of course. Here is the updated README, focusing only on the Docker setup instructions and the API request/response formats.

-----

# Semantic Question Similarity API


## API Endpoint Details

**Note**: Protected endpoints require an `Authorization: Bearer <your_access_token>` header.

### `POST /login`

  * **Request Body**:
    ```json
    {
      "username": "webapp_admin",
      "password": "your_strong_password"
    }
    ```
  * **Success Response (200 OK)**:
    ```json
    {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

-----

Of course. Here are the updated request and response formats.

The main change is adding optional fields (`embedding_provider`, `reasoning_provider`) to the request bodies. This allows you to specify which AI provider to use for the analysis, making the API more flexible.

-----

### `POST /check_similarity`

Checks if a new question is semantically similar to any question from a list hosted at a given URL.

  * **Request Body**:

    ```json
    {
      "questions_url": "https://example.com/api/questions.json",
      "question": "How do I set up a Docker container?",
      "embedding_provider": "openai",
      "reasoning_provider": "gemini"
    }
    ```

      * **`embedding_provider`** (optional): Specifies the AI service for generating embeddings. Supported values: `gemini`, `openai`. Defaults to the server's pre-configured provider if omitted.
      * **`reasoning_provider`** (optional): Specifies the AI service for initial question validation. Supported values: `gemini`, `openai`, `deepseek`. Defaults to the server's pre-configured provider if omitted.

  * **Success Response (Match Found)**:

    ```json
    {
      "response": "yes",
      "matched_questions": [
        {
          "Question": "What are the steps to configure a Docker container?",
          "Answer": "First, you need to create a Dockerfile..."
        }
      ]
    }
    ```

  * **Success Response (No Match Found)**:

    ```json
    {
      "response": "no"
    }
    ```

-----

### `POST /group_similar_questions`

Fetches all questions from a URL and groups them into clusters of semantically similar questions.

  * **Request Body**:

    ```json
    {
      "questions_url": "https://example.com/api/questions.json",
      "embedding_provider": "gemini"
    }
    ```

      * **`embedding_provider`** (optional): Specifies the AI service for generating embeddings. Supported values: `gemini`, `openai`. Defaults to the server's pre-configured provider if omitted.

  * **Success Response (Groups Found)**:

    ```json
    {
      "response": "yes",
      "matched_groups": [
        [
          { "Question": "Question A1", "Answer": "..." },
          { "Question": "Question A2", "Answer": "..." }
        ],
        [
          { "Question": "Question B1", "Answer": "..." },
          { "Question": "Question B2", "Answer": "..." }
        ]
      ]
    }
    ```

  * **Success Response (No Groups Found)**:

    ```json
    {
      "response": "no"
    }
    ```