import os
import sys
import pytest
import sqlite3
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import shutil

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from main import app, init_db, UPLOAD_DIR, DATABASE_FILE

client = TestClient(app)

TEST_DB = "test_transcriptions.db"
TEST_UPLOAD_DIR = "test_uploads"

@pytest.fixture(autouse=True)
def setup_and_teardown():

    os.makedirs(TEST_UPLOAD_DIR, exist_ok=True)
    
    with patch("main.DATABASE_FILE", TEST_DB), \
         patch("main.UPLOAD_DIR", TEST_UPLOAD_DIR):
        
        init_db()
        
        yield 
        
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)
        if os.path.exists(TEST_UPLOAD_DIR):
            shutil.rmtree(TEST_UPLOAD_DIR)

# Mock the Whisper transcription function
@pytest.fixture
def mock_transcribe():
    with patch("main.transcribe_with_whisper", return_value="This is a test transcription."):
        yield

# Test uploading non-audio file
def test_upload_non_audio_file():
    # Create a test text file
    test_file_content = b"This is not an audio file"
    
    response = client.post(
        "/transcribe",
        files={"audio_file": ("test.txt", test_file_content, "text/plain")}
    )
    
    assert response.status_code == 500
    assert "not an audio file" in response.json()["detail"]

# Test get all transcriptions endpoint
def test_get_all_transcriptions():
    # First, insert some test data
    with patch("main.DATABASE_FILE", TEST_DB):
        conn = sqlite3.connect(TEST_DB)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO transcriptions (original_filename, unique_filename, transcription) VALUES (?, ?, ?)",
            ("test1.mp3", "test1_abc123.mp3", "Test transcription 1")
        )
        cursor.execute(
            "INSERT INTO transcriptions (original_filename, unique_filename, transcription) VALUES (?, ?, ?)",
            ("test2.mp3", "test2_def456.mp3", "Test transcription 2")
        )
        conn.commit()
        conn.close()
        
        # Now test the endpoint
        response = client.get("/transcriptions")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
        assert response.json()[0]["original_filename"] == "test1.mp3"  # Most recent first
        assert response.json()[1]["original_filename"] == "test2.mp3"

# Test transcribe endpoint with mock audio file
def test_transcribe_endpoint(mock_transcribe):
    # Create a test audio file
    test_file_content = b"mock audio data"
    
    with patch("main.DATABASE_FILE", TEST_DB), \
         patch("main.UPLOAD_DIR", TEST_UPLOAD_DIR):
         
        response = client.post(
            "/transcribe",
            files={"audio_file": ("test_audio.mp3", test_file_content, "audio/mpeg")}
        )
        
        assert response.status_code == 200
        assert "transcription" in response.json()
        assert response.json()["transcription"] == "This is a test transcription."
        assert response.json()["original_filename"] == "test_audio.mp3"
        assert "unique_filename" in response.json()