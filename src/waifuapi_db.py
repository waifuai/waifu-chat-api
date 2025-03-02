import sqlite3
import time
import datetime
import os
from typing import Optional

# Use a module-level connection pool
db_file: str = os.environ.get('DATABASE_FILE', 'dialogs.db')
connection_pool: list[sqlite3.Connection] = []
pool_size: int = 5  # Adjust pool size as needed

def get_connection() -> sqlite3.Connection:
    """Gets a connection from the connection pool."""
    if connection_pool:
        return connection_pool.pop()
    else:
        return sqlite3.connect(db_file, timeout=5)


def release_connection(conn: sqlite3.Connection):
    """Releases a connection back to the connection pool."""
    if len(connection_pool) < pool_size:
        connection_pool.append(conn)
    else:
        conn.close()


def get_old_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the previous dialog for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        dialog: str = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        dialog = ""  # Return empty string on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return dialog


def update_user_dialog(current_user: str, user_id: str, dialog: str) -> None:
    """Updates the dialog for a given user."""
    last_modified_datetime: str = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_modified_timestamp: int = int(time.time())
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('UPDATE dialogs SET dialog=?, last_modified_datetime=?, last_modified_timestamp=? WHERE current_user=? AND user_id=?', (dialog, last_modified_datetime, last_modified_timestamp, current_user, user_id,))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)


def reset_user_chat(current_user: str, user_id: str) -> None:
    """Resets the dialog for a given user to an empty string."""
    update_user_dialog(current_user=current_user, user_id=user_id, dialog='')


def is_user_id_in_db(current_user: str, user_id: str) -> bool:
    """Checks if a user ID exists in the database."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT 1 FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        result: bool = True if result_tuple else False
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        result = False  # Assume user doesn't exist on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return result


def add_user_to_db(current_user: str, user_id: str) -> None:
    """Adds a new user to the database with an empty dialog."""
    last_modified_datetime: str = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    last_modified_timestamp: int = int(time.time())
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO dialogs (current_user, user_id, dialog, last_modified_datetime, last_modified_timestamp) VALUES (?, ?, ?, ?, ?)', (current_user, user_id, '', last_modified_datetime, last_modified_timestamp,))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)


def delete_user_from_db(current_user: str, user_id: str) -> None:
    """Deletes a user from the database."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('DELETE FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)


def get_user_count(current_user: str) -> int:
    """Gets the total number of users for a given WaifuAPI user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT COUNT(*) FROM dialogs WHERE current_user=?', (current_user,))
        result_tuple = cursor.fetchone()
        result: int = result_tuple[0] if result_tuple else 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        result = 0  # Assume 0 users on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return result


def get_all_users(current_user: str) -> list[str]:
    """Gets a list of all user IDs for a given WaifuAPI user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id FROM dialogs WHERE current_user=?', (current_user,))
        result_tuple = cursor.fetchall()
        result: list[str] = [user_id[0] for user_id in result_tuple]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        result = []  # Return empty list on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return result


def get_all_users_paged(current_user: str, page: int) -> list[str]:
    """Gets a page of user IDs for a given WaifuAPI user, ordered by last modified timestamp."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT user_id FROM dialogs WHERE current_user=? ORDER BY last_modified_timestamp DESC LIMIT ?, 100', (current_user, page * 100,))
        result_tuple = cursor.fetchall()
        result: list[str] = [user_id[0] for user_id in result_tuple]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        result = []  # Return empty list on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return result


def get_user_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the dialog for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        dialog: str = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        dialog = ""  # Return empty string on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return dialog


def get_user_last_modified_datetime(current_user: str, user_id: str) -> str:
    """Retrieves the last modified datetime for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT last_modified_datetime FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        last_modified_datetime: str = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        last_modified_datetime = ""  # Return empty string on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return last_modified_datetime


def get_user_last_modified_timestamp(current_user: str, user_id: str) -> int:
    """Retrieves the last modified timestamp for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT last_modified_timestamp FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        last_modified_timestamp: int = result_tuple[0] if result_tuple else 0
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        last_modified_timestamp = 0  # Return 0 on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return last_modified_timestamp


def get_user_context(current_user: str, user_id: str) -> str:
    """Retrieves the context for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('SELECT context FROM dialogs WHERE current_user=? AND user_id=?', (current_user, user_id,))
        result_tuple = cursor.fetchone()
        context: str = result_tuple[0] if result_tuple else ""
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        context = ""  # Return empty string on error
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)
    return context


def set_user_context(current_user: str, user_id: str, context: str) -> None:
    """Sets the context for a given user."""
    conn: sqlite3.Connection = get_connection()
    cursor: sqlite3.Cursor = conn.cursor()
    try:
        cursor.execute('UPDATE dialogs SET context=? WHERE current_user=? AND user_id=?', (context, current_user, user_id,))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.commit()
        release_connection(conn)