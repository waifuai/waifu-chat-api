import pytest
import os
import tempfile
import sqlite3
from dotenv import load_dotenv
load_dotenv()

import flask
from src.waifuapi import app
from src import waifuapi_db

# Override the database file for testing
TEST_DATABASE_FILE = "test_dialogs.db"
os.environ['DATABASE_FILE'] = TEST_DATABASE_FILE

@pytest.fixture
def client():
    """Flask app test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create a test database and tables."""
    # Ensure the test database file does not exist
    if os.path.exists(TEST_DATABASE_FILE):
        os.remove(TEST_DATABASE_FILE)

    # Create a connection to the test database
    conn = sqlite3.connect(TEST_DATABASE_FILE)
    cursor = conn.cursor()

    # Create the dialogs table
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
    cursor.close()
    conn.close()

    yield  # Provide the fixture value

    # Teardown: Remove the test database file after the tests
    if os.path.exists(TEST_DATABASE_FILE):
        os.remove(TEST_DATABASE_FILE)