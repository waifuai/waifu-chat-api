"""
Improved database module with connection pooling and better error handling for WaifuAPI.
"""
import sqlite3
import time
import datetime
import os
import threading
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from flask import current_app, g

from .waifuapi_logging import get_logger, handle_exception
from .waifuapi_config import get_app_config

logger = get_logger("database")


class DatabasePool:
    """Connection pool for SQLite database connections."""

    def __init__(self, db_path: str, max_connections: int = 10, timeout: float = 5.0):
        self.db_path = db_path
        self.max_connections = max_connections
        self.timeout = timeout
        self._connections = []
        self._lock = threading.Lock()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection from the pool."""
        with self._lock:
            # Try to find an available connection
            for conn in self._connections:
                if not conn['in_use']:
                    conn['in_use'] = True
                    return conn['connection']

            # Create new connection if pool is not full
            if len(self._connections) < self.max_connections:
                try:
                    connection = sqlite3.connect(self.db_path, timeout=self.timeout)
                    connection.execute("PRAGMA journal_mode=WAL")
                    connection.execute("PRAGMA synchronous=NORMAL")
                    connection.execute("PRAGMA cache_size=-64000")  # 64MB cache

                    self._connections.append({
                        'connection': connection,
                        'in_use': True
                    })
                    logger.debug(f"Created new database connection. Pool size: {len(self._connections)}")
                    return connection
                except sqlite3.Error as e:
                    logger.error(f"Failed to create database connection: {e}")
                    raise

            # Wait for an available connection
            raise sqlite3.Error("Connection pool exhausted")

    def release_connection(self, connection: sqlite3.Connection) -> None:
        """Release a connection back to the pool."""
        with self._lock:
            for conn in self._connections:
                if conn['connection'] == connection:
                    conn['in_use'] = False
                    break

    def close_all(self) -> None:
        """Close all connections in the pool."""
        with self._lock:
            for conn in self._connections:
                try:
                    conn['connection'].close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            self._connections.clear()
        logger.info("All database connections closed")


# Global connection pool
_db_pool: Optional[DatabasePool] = None


def init_db_pool() -> None:
    """Initialize the database connection pool."""
    global _db_pool

    try:
        config = get_app_config()
        db_path = config.database_file
    except Exception:
        db_path = os.environ.get('DATABASE_FILE', 'dialogs.db')

    # Ensure database directory exists
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else '.', exist_ok=True)

    _db_pool = DatabasePool(db_path)
    logger.info(f"Database connection pool initialized for: {db_path}")


def get_db_pool() -> DatabasePool:
    """Get the database connection pool."""
    if _db_pool is None:
        init_db_pool()
    return _db_pool


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    pool = get_db_pool()
    conn = None
    try:
        conn = pool.get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            pool.release_connection(conn)


def init_database_tables() -> None:
    """Initialize database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Create dialogs table with improved schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                current_user TEXT NOT NULL,
                user_id TEXT NOT NULL,
                dialog TEXT,
                last_modified_datetime TEXT,
                last_modified_timestamp INTEGER,
                context TEXT,
                PRIMARY KEY (current_user, user_id)
            )
        """)

        # Create indexes for better performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dialogs_current_user
            ON dialogs(current_user)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_dialogs_timestamp
            ON dialogs(last_modified_timestamp DESC)
        """)

        logger.info("Database tables initialized")


def get_old_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the previous dialog for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else ""
    except sqlite3.Error as e:
        logger.error(f"Database error in get_old_dialog: {e}")
        raise


def update_user_dialog(current_user: str, user_id: str, dialog: str) -> None:
    """Updates the dialog for a given user."""
    last_modified_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_modified_timestamp = int(time.time())

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT OR REPLACE INTO dialogs
                   (current_user, user_id, dialog, last_modified_datetime, last_modified_timestamp, context)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (current_user, user_id, dialog, last_modified_datetime, last_modified_timestamp, None)
            )
        logger.debug(f"Dialog updated for user: {user_id}")
    except sqlite3.Error as e:
        logger.error(f"Database error in update_user_dialog: {e}")
        raise


def reset_user_chat(current_user: str, user_id: str) -> None:
    """Resets the dialog for a given user to an empty string."""
    update_user_dialog(current_user, user_id, '')


def is_user_id_in_db(current_user: str, user_id: str) -> bool:
    """Checks if a user ID exists in the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT 1 FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result is not None
    except sqlite3.Error as e:
        logger.error(f"Database error in is_user_id_in_db: {e}")
        raise


def add_user_to_db(current_user: str, user_id: str) -> None:
    """Adds a new user to the database with an empty dialog."""
    last_modified_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_modified_timestamp = int(time.time())

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''INSERT OR IGNORE INTO dialogs
                   (current_user, user_id, dialog, last_modified_datetime, last_modified_timestamp, context)
                   VALUES (?, ?, ?, ?, ?, ?)''',
                (current_user, user_id, '', last_modified_datetime, last_modified_timestamp, None)
            )
        logger.debug(f"User added to database: {user_id}")
    except sqlite3.Error as e:
        logger.error(f"Database error in add_user_to_db: {e}")
        raise


def get_user_count(current_user: str) -> int:
    """Gets the total number of users for a given WaifuAPI user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) FROM dialogs WHERE current_user=?',
                (current_user,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_count: {e}")
        raise


def get_all_users(current_user: str) -> List[str]:
    """Gets a list of all user IDs for a given WaifuAPI user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_id FROM dialogs WHERE current_user=? ORDER BY last_modified_timestamp DESC',
                (current_user,)
            )
            results = cursor.fetchall()
            return [row[0] for row in results]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_all_users: {e}")
        raise


def get_all_users_paged(current_user: str, page: int, page_size: int = 100) -> List[str]:
    """Gets a page of user IDs for a given WaifuAPI user, ordered by last modified timestamp."""
    offset = page * page_size
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT user_id FROM dialogs
                   WHERE current_user=? ORDER BY last_modified_timestamp DESC
                   LIMIT ? OFFSET ?''',
                (current_user, page_size, offset)
            )
            results = cursor.fetchall()
            return [row[0] for row in results]
    except sqlite3.Error as e:
        logger.error(f"Database error in get_all_users_paged: {e}")
        raise


def get_user_dialog(current_user: str, user_id: str) -> str:
    """Retrieves the dialog for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT dialog FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else ""
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_dialog: {e}")
        raise


def get_user_last_modified_datetime(current_user: str, user_id: str) -> str:
    """Retrieves the last modified datetime for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT last_modified_datetime FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else ""
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_last_modified_datetime: {e}")
        raise


def get_user_last_modified_timestamp(current_user: str, user_id: str) -> int:
    """Retrieves the last modified timestamp for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT last_modified_timestamp FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_last_modified_timestamp: {e}")
        raise


def get_user_context(current_user: str, user_id: str) -> str:
    """Retrieves the context for a given user."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT context FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else ""
    except sqlite3.Error as e:
        logger.error(f"Database error in get_user_context: {e}")
        raise


def set_user_context(current_user: str, user_id: str, context: str) -> None:
    """Sets the context for a given user."""
    last_modified_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_modified_timestamp = int(time.time())

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''UPDATE dialogs SET context=?, last_modified_datetime=?, last_modified_timestamp=?
                   WHERE current_user=? AND user_id=?''',
                (context, last_modified_datetime, last_modified_timestamp, current_user, user_id)
            )
        logger.debug(f"Context updated for user: {user_id}")
    except sqlite3.Error as e:
        logger.error(f"Database error in set_user_context: {e}")
        raise


def delete_user_from_db(current_user: str, user_id: str) -> None:
    """Deletes a user from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'DELETE FROM dialogs WHERE current_user=? AND user_id=?',
                (current_user, user_id,)
            )
        logger.info(f"User deleted from database: {user_id}")
    except sqlite3.Error as e:
        logger.error(f"Database error in delete_user_from_db: {e}")
        raise


def cleanup_old_connections() -> None:
    """Clean up old database connections."""
    if _db_pool:
        _db_pool.close_all()


# Flask teardown function
def close_db(e=None):
    """Close database connections when the app context ends."""
    cleanup_old_connections()