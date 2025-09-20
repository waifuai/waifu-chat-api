"""
Database operations module for WaifuAPI.
This module provides direct SQLite database operations for managing user dialogs,
including creating, updating, retrieving, and deleting user data and dialog history.
Uses direct SQLite connections with proper error handling and transaction management.
"""
import sqlite3
import time
import datetime
import os
from flask import current_app # Import current_app
from typing import Optional

# Removed module-level db_file, connection_pool, and pool management functions

def _get_db_path() -> str:
    """Gets the database path from the current Flask app config."""
    try:
        return current_app.config['DATABASE_FILE']
    except RuntimeError:
        # Handle cases where code might be called outside app context (e.g., setup scripts)
        # Fallback to environment variable or default if no app context
        print("Warning: Accessing DB path outside Flask app context. Falling back to env var/default.")
        return os.environ.get('DATABASE_FILE', 'dialogs.db')

# No longer using a pool, but Flask needs a function to call for teardown context
def close_db(e=None):
    # Since we use 'with sqlite3.connect()', connections are closed automatically.
    # This function can be a no-op or log teardown.
    # print("Tearing down app context - DB connections managed by 'with'.")
    pass


def get_old_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the previous dialog for a given user."""
    db_path = _get_db_path()
    dialog: str = ""
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            dialog = result_tuple[0] if result_tuple else ""
            # No need for explicit cursor.close() or conn.commit() with 'with' for SELECT
    except sqlite3.Error as e:
        print(f"Database error in get_old_dialog: {e}")
        raise # Re-raise the exception
    return dialog


def update_user_dialog(current_user: str, user_id: str, dialog: str) -> None:
    """Updates the dialog for a given user."""
    db_path = _get_db_path()
    last_modified_datetime: str = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_modified_timestamp: int = int(time.time())
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('UPDATE dialogs SET dialog=?, last_modified_datetime=?, last_modified_timestamp=? WHERE current_user=? AND user_id=?', (dialog, last_modified_datetime, last_modified_timestamp, current_user, user_id,))
            # conn.commit() is called automatically by 'with' on success
    except sqlite3.Error as e:
        print(f"Database error in update_user_dialog: {e}")
        raise # Re-raise the exception


def reset_user_chat(current_user: str, user_id: str) -> None:
    """Resets the dialog for a given user to an empty string."""
    update_user_dialog(current_user=current_user, user_id=user_id, dialog='')


def is_user_id_in_db(current_user: str, user_id: str) -> bool:
    """Checks if a user ID exists in the database."""
    db_path = _get_db_path()
    result: bool = False
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            result = True if result_tuple else False
    except sqlite3.Error as e:
        print(f"Database error in is_user_id_in_db: {e}")
        raise # Re-raise the exception
    return result


def add_user_to_db(current_user: str, user_id: str) -> None:
    """Adds a new user to the database with an empty dialog."""
    db_path = _get_db_path()
    last_modified_datetime: str = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_modified_timestamp: int = int(time.time())
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('INSERT INTO dialogs (current_user, user_id, dialog, last_modified_datetime, last_modified_timestamp) VALUES (?, ?, ?, ?, ?)', (current_user, user_id, '', last_modified_datetime, last_modified_timestamp,))
    except sqlite3.Error as e:
        print(f"Database error in add_user_to_db: {e}")
        raise # Re-raise the exception


def delete_user_from_db(current_user: str, user_id: str) -> None:
    """Deletes a user from the database."""
    db_path = _get_db_path()
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('DELETE FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
    except sqlite3.Error as e:
        print(f"Database error in delete_user_from_db: {e}")
        raise # Re-raise the exception


def get_user_count(current_user: str) -> int:
    """Gets the total number of users for a given WaifuAPI user."""
    db_path = _get_db_path()
    result: int = 0
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM dialogs WHERE current_user=?', (current_user,))
            result_tuple = cursor.fetchone()
            result = result_tuple[0] if result_tuple else 0
    except sqlite3.Error as e:
        print(f"Database error in get_user_count: {e}")
        raise # Re-raise the exception
    return result


def get_all_users(current_user: str) -> list[str]:
    """Gets a list of all user IDs for a given WaifuAPI user."""
    db_path = _get_db_path()
    result: list[str] = []
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM dialogs WHERE current_user=?', (current_user,))
            result_tuple = cursor.fetchall()
            result = [user_id[0] for user_id in result_tuple]
    except sqlite3.Error as e:
        print(f"Database error in get_all_users: {e}")
        raise # Re-raise the exception
    return result


def get_all_users_paged(current_user: str, page: int) -> list[str]:
    """Gets a page of user IDs for a given WaifuAPI user, ordered by last modified timestamp."""
    db_path = _get_db_path()
    result: list[str] = []
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT user_id FROM dialogs WHERE current_user=? ORDER BY last_modified_timestamp DESC LIMIT ?, 100', (current_user, page * 100,))
            result_tuple = cursor.fetchall()
            result = [user_id[0] for user_id in result_tuple]
    except sqlite3.Error as e:
        print(f"Database error in get_all_users_paged: {e}")
        raise # Re-raise the exception
    return result


def get_user_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the dialog for a given user."""
    db_path = _get_db_path()
    dialog: str = ""
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            dialog = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error in get_user_dialog: {e}")
        raise # Re-raise the exception
    return dialog


def get_user_last_modified_datetime(current_user: str, user_id: str) -> str:
    """Retrieves the last modified datetime for a given user."""
    db_path = _get_db_path()
    last_modified_datetime: str = ""
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT last_modified_datetime FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            last_modified_datetime = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error in get_user_last_modified_datetime: {e}")
        raise # Re-raise the exception
    return last_modified_datetime


def get_user_last_modified_timestamp(current_user: str, user_id: str) -> int:
    """Retrieves the last modified timestamp for a given user."""
    db_path = _get_db_path()
    last_modified_timestamp: int = 0
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT last_modified_timestamp FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            last_modified_timestamp = result_tuple[0] if result_tuple else 0
    except sqlite3.Error as e:
        print(f"Database error in get_user_last_modified_timestamp: {e}")
        raise # Re-raise the exception
    return last_modified_timestamp


def get_user_context(current_user: str, user_id: str) -> str:
    """Retrieves the context for a given user."""
    db_path = _get_db_path()
    context: str = ""
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('SELECT context FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
            result_tuple = cursor.fetchone()
            context = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error in get_user_context: {e}")
        raise # Re-raise the exception
    return context


def set_user_context(current_user: str, user_id: str, context: str) -> None:
    """Sets the context for a given user."""
    db_path = _get_db_path()
    try:
        with sqlite3.connect(db_path, timeout=5) as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            cursor.execute('UPDATE dialogs SET context=? WHERE current_user=? AND user_id=?', (context, current_user, user_id,))
    except sqlite3.Error as e:
        print(f"Database error in set_user_context: {e}")
        raise # Re-raise the exception