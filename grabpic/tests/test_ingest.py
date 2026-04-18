import pytest
from httpx import AsyncClient
from grabpic.main import app
import os

@pytest.mark.asyncio
async def test_ingest_no_face():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        # Using a tiny black image or something that definitely has no faces
        files = {'file': ('test.jpg', b'\x00' * 100, 'image/jpeg')}
        response = await ac.post("/ingest", files=files)
    
    # DeepFace will likely fail to detect a face in 100 null bytes
    assert response.status_code == 422
    assert "No faces detected" in response.json()['detail']

@pytest.mark.asyncio
async def test_invalid_grab_id():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = await ac.get(f"/images/{non_existent_id}")
    
    assert response.status_code == 404
    assert "No images found" in response.json()['detail']
