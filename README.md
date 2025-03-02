# waifu chat api

## Table of Contents
1.  [Project Description and Purpose](#project-description-and-purpose)
2.  [Installation and Setup Instructions](#installation-and-setup-instructions)
3.  [API Documentation](#api-documentation)
    *   [User Management](#user-management)
    *   [Dialog Management](#dialog-management)
    *   [Server Status](#server-status)
4.  [Configuration](#configuration)
5.  [Troubleshooting](#troubleshooting)

## Project Description and Purpose

This project is a Flask-based API for interacting with a conversational AI waifu character. It provides endpoints for user management, dialog management, and server status checks.

This project provides a backend API for a conversational AI. It allows users to interact with the AI, manage their dialog history, and check the server status. The API is designed to be flexible and extensible, allowing for future integration with different AI models and front-end applications.

## Installation and Setup Instructions

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd waifu-chat-api
    ```
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt --user
    ```
    You may create a `requirements.txt` by running:
    ```bash
    pip freeze > requirements.txt
    ```

3.  **Set environment variables:**

    The API relies on environment variables for configuration. You can set these variables directly in your terminal or, preferably, using a `.env` file.

    *   `DATABASE_FILE`: Path to the SQLite database file (default: `dialogs.db`). This file stores user dialog history.
    *   `MODEL_URL`: URL of the AI model endpoint (default: `http://localhost:80/path/`). This is the address where the API sends requests to generate responses.
    *   `DEFAULT_RESPONSE`: The default response message when the AI model is unavailable or returns an error (default: "The AI model is currently unavailable. Please try again later.").
    *   `DEFAULT_GENRE`: The default genre for the conversation (default: "Romance").

    **Example using a `.env` file (recommended):**

    1.  Create a `.env` file in the project root:

        ```
        DATABASE_FILE=dialogs.db
        MODEL_URL=http://localhost:80/path/
        DEFAULT_RESPONSE="I'm sorry, I'm having trouble connecting to the AI model."
        DEFAULT_GENRE="Fantasy"
        ```
    2.  Install `python-dotenv`:
        ```bash
        pip install python-dotenv --user
        ```
    3.  Add the following lines to the top of `src/waifuapi.py` to load the environment variables:
        ```python
        from dotenv import load_dotenv
        load_dotenv()
        ```

4.  **Run the application:**

    ```bash
    python src/waifuapi.py
    ```
    The default port is 5000. You can specify a different port by setting the `PORT` environment variable.

    To run the application in different environments:

    *   **Development:** Run the application as shown above.
    *   **Testing:** Use a testing framework like `pytest` (see the Testing section below).
    *   **Production:** Use a production-ready WSGI server like Gunicorn or uWSGI.

    **Note:** The API uses the `current-user` header to identify the user making the request. This header is used to distinguish between different WaifuAPI users, allowing each user to have their own set of users and dialog history. If this header is not provided, the API defaults to a generic user ID.

## API Documentation

The API provides the following endpoints:

### User Management

*   `/v1/user/id/<user_id>` (PUT): Create a user.
    *   Description: Creates a new user with the given user ID.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user to create.
    *   Example Request: `PUT /v1/user/id/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user"}
        ```
*   `/v1/user/id/<user_id>` (GET): Check if a user exists.
    *   Description: Checks if a user with the given user ID exists.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user to check.
    *   Example Request: `GET /v1/user/id/test_user`
    *   Example Response (User exists):
        ```json
        {"user_id": "test_user", "exists": true}
        ```
    *   Example Response (User does not exist):
        ```json
        {"user_id": "test_user", "exists": false}
        ```
*   `/v1/user/metadata/<user_id>` (GET): Get user metadata (last modified datetime and timestamp).
    *   Description: Retrieves metadata for a user, including the last modified datetime and timestamp.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user.
    *   Example Request: `GET /v1/user/metadata/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user", "last_modified_datetime": "2025-03-01 11:22:33", "last_modified_timestamp": 1740828153}
        ```
*   `/v1/user/id/<user_id>` (DELETE): Delete a user.
    *   Description: Deletes a user with the given user ID.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user to delete.
    *   Example Request: `DELETE /v1/user/id/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user"}
        ```
*   `/v1/user/all/count` (GET): Get the total number of users.
    *   Description: Retrieves the total number of users.
    *   Example Request: `GET /v1/user/all/count`
    *   Example Response:
        ```json
        {"user_count": 5}
        ```
*   `/v1/user/all/id/<int:page>` (GET): Get all users, paged by hundreds.
    *   Description: Retrieves a page of user IDs, with each page containing up to 100 users.
    *   Request Parameters:
        *   `page` (integer, required): The page number to retrieve (0-indexed).
    *   Example Request: `GET /v1/user/all/id/0`
    *   Example Response:
        ```json
        {"page": 0, "users": ["user1", "user2", "user3"]}
        ```

### Dialog Management

*   `/v1/user/dialog/<user_id>` (DELETE): Reset user dialog.
    *   Description: Resets the dialog history for a given user.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user.
    *   Example Request: `DELETE /v1/user/dialog/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user"}
        ```
*   `/v1/user/dialog/json/<user_id>` (GET): Get user dialog in JSON format.
    *   Description: Retrieves the dialog history for a user in JSON format.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user.
    *   Example Request: `GET /v1/user/dialog/json/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user", "dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
        ```
*   `/v1/user/dialog/json/<user_id>` (PUT): Set user dialog in JSON format.
    *   Description: Sets the dialog history for a user using a JSON object.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user.
    *   Request Body:
        ```json
        {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
        ```
    *   Example Request: `PUT /v1/user/dialog/json/test_user`
    *   Example Request Body:
        ```json
        {"dialog": [{"index": 0, "name": "User", "message": "Hello"}, {"index": 1, "name": "Waifu", "message": "Hi"}]}
        ```
    *   Example Response:
        ```json
        {"user_id": "test_user"}
        ```
*   `/v1/user/dialog/str/<user_id>` (GET): Get user dialog as a string.
    *   Description: Retrieves the dialog history for a user as a string.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user.
    *   Example Request: `GET /v1/user/dialog/str/test_user`
    *   Example Response:
        ```json
        {"user_id": "test_user", "dialog": "User said: \"Hello\" Waifu said: \"Hi\""}
        ```
*   `/path` (POST): Send a chat message (using form data).
    *   Description: Sends a chat message to the AI using form data.
    *   Request Parameters:
        *   `message` (string, required): The chat message to send.
        *   `user_id` (string, required): The ID of the user sending the message.
    *   Example Request: `POST /path message=Hello&user_id=test_user`
    *   Example Response: `Hi`
*   `/v1/waifu` (POST): Send a chat message (using JSON data).
    *   Description: Sends a chat message to the AI using JSON data.
    *   Request Parameters:
        *   `user_id` (string, required): The ID of the user sending the message.
        *   `message` (string, required): The chat message to send.
    *   Example Request: `POST /v1/waifu`
    *   Example Request Body:
        ```json
        {"user_id": "test_user", "message": "Hello"}
        ```
    *   Example Response:
        ```json
        {"user_id": "test_user", "response": "Hi"}
        ```

### Server Status

*   `/v1/server/status` (GET): Check server status.
    *   Description: Checks the status of the server.
    *   Example Request: `GET /v1/server/status`
    *   Example Response:
        ```json
        {"status": "ok"}
        ```

### HTTP Methods

The API uses the following HTTP methods:

*   `GET`: Used to retrieve data from the server.
*   `PUT`: Used to create or update data on the server.
*   `POST`: Used to send data to the server to create or update a resource.
*   `DELETE`: Used to delete data from the server.

## Configuration

The API can be configured using environment variables. The following environment variables are supported:

*   `DATABASE_FILE`: Path to the SQLite database file (default: `dialogs.db`).
*   `MODEL_URL`: URL of the AI model endpoint (default: `http://localhost:80/path/`).
*   `DEFAULT_RESPONSE`: The default response message when the AI model is unavailable or returns an error (default: "The AI model is currently unavailable. Please try again later.").
*   `DEFAULT_GENRE`: The default genre for the conversation (default: "Romance").


## Troubleshooting

*   **"ModuleNotFoundError: No module named 'google.cloud'":**
    *   Make sure you have installed the Google Cloud Translate library:
        ```bash
        pip install google-cloud-translate --user
        ```
    *   Ensure that you have set up your Google Cloud credentials correctly.

*   **API returns "The AI model is currently unavailable. Please try again later." unexpectedly:**
    *   This is a default response when the AI model is unavailable or returns an error. Check the `MODEL_URL` environment variable and make sure the AI model is running correctly. Also check the `DEFAULT_RESPONSE` environment variable.

*   **The conversation genre is not what I expected:**
    *   Check the `DEFAULT_GENRE` environment variable.
