import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from grabpic.main import app

client = TestClient(app)

# 1. Test standard FastAPI validation
def test_ingest_no_file():
    response = client.post("/ingest")
    assert response.status_code == 422

# 2. Test DeepFace exception handling
def test_ingest_corrupt_file():
    # Sending null bytes to simulate a non-image file
    files = {'file': ('test.jpg', b'\x00' * 100, 'image/jpeg')}
    response = client.post("/ingest", files=files)
    assert response.status_code == 422
    assert "Invalid or unreadable" in response.json()['detail'] or "No faces detected" in response.json()['detail']

# 3. Test successful ingestion logic (Mocking DB & DeepFace)
@patch('grabpic.main.supabase')
@patch('grabpic.main.DeepFace.represent')
def test_ingest_success(mock_deepface, mock_supabase):
    # Mock DeepFace returning one face
    mock_deepface.return_value = [{'embedding': [0.1] * 128}]
    
    # Mock Supabase RPC (simulate face NOT found in DB so it creates a new one)
    mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
    
    files = {'file': ('test.jpg', b'fake_image_data', 'image/jpeg')}
    response = client.post("/ingest", files=files)
    
    assert response.status_code == 200
    assert response.json()['faces_detected'] == 1
    assert len(response.json()['grab_ids']) == 1

# 4. Test successful auth match
@patch('grabpic.main.supabase')
@patch('grabpic.main.DeepFace.represent')
def test_auth_success(mock_deepface, mock_supabase):
    mock_deepface.return_value = [{'embedding': [0.1] * 128}]
    
    # Mock Supabase returning a high similarity match
    fake_uuid = "123e4567-e89b-12d3-a456-426614174000"
    mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[{'grab_id': fake_uuid, 'similarity': 0.85}])
    
    files = {'file': ('selfie.jpg', b'fake_image_data', 'image/jpeg')}
    response = client.post("/auth", files=files)
    
    assert response.status_code == 200
    assert response.json()['authenticated'] is True
    assert response.json()['grab_id'] == fake_uuid

# 5. Test auth mismatch (Unrecognized face)
@patch('grabpic.main.supabase')
@patch('grabpic.main.DeepFace.represent')
def test_auth_mismatch(mock_deepface, mock_supabase):
    mock_deepface.return_value = [{'embedding': [0.9] * 128}]
    
    # Mock Supabase finding NO match above the threshold
    mock_supabase.rpc.return_value.execute.return_value = MagicMock(data=[])
    
    files = {'file': ('selfie.jpg', b'fake_image_data', 'image/jpeg')}
    response = client.post("/auth", files=files)
    
    assert response.status_code == 401
    assert "Selfie mismatch" in response.json()['detail']