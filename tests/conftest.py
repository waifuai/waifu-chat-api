import pytest
import os
import tempfile
import sqlite3
import time # Added for delay
import gc # Import garbage collector
from dotenv import load_dotenv
from unittest import mock # Import mock

load_dotenv()

import flask
# Import the factory function instead of the global app
from src.waifuapi import create_app

# Override the database file for testing
TEST_DATABASE_FILE = "test_dialogs.db"


@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    # Create the app instance with test config
    app = create_app({
        'TESTING': True,
        'DATABASE_FILE': TEST_DATABASE_FILE,
    })
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

# This fixture now ONLY handles table creation and file cleanup
@pytest.fixture(scope="function", autouse=True)
def init_test_database():
    """Ensures the test database file exists and has the correct table."""
    # --- Setup ---
    # Ensure the test database file does not exist before creating it
    if os.path.exists(TEST_DATABASE_FILE):
        try:
            os.remove(TEST_DATABASE_FILE)
        except PermissionError as e:
            print(f"Initial PermissionError removing old test db (will proceed): {e}")
        except Exception as e:
             print(f"Initial Error removing old test db (will proceed): {e}")

    # Create table using a direct connection to the test file
    conn = None
    cursor = None
    try:
        conn = sqlite3.connect(TEST_DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dialogs (
                current_user TEXT NOT NULL,
                user_id TEXT NOT NULL,
                dialog TEXT,
                last_modified_datetime TEXT,
                last_modified_timestamp INTEGER,
                context TEXT
            )
        """)
        conn.commit()
    except Exception as e:
        print(f"Error during test database table creation: {e}")
        raise # Re-raise the exception to fail the setup if table creation fails
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close() # Close the direct connection used for setup

    yield # Test runs here

    # --- Teardown --- (occurs after yield)
    # Force garbage collection before attempting file deletion
    gc.collect()
    # Remove the test database file with retries
    attempts = 5
    while attempts > 0:
        try:
            if os.path.exists(TEST_DATABASE_FILE):
                os.remove(TEST_DATABASE_FILE)
                print(f"Successfully removed {TEST_DATABASE_FILE}")
            break # Success
        except PermissionError as e:
            attempts -= 1
            if attempts == 0:
                print(f"Failed to remove test database file after multiple attempts: {e}")
            else:
                print(f"PermissionError removing test db, retrying in 0.5s... ({attempts} attempts left)")
                time.sleep(0.5)
        except Exception as e:
            print(f"Error during test database teardown: {e}")
            break # Don't retry on other errors