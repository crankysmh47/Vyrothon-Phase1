"""
Unit tests for the GRABPIC image ingestion and retrieval endpoints.
"""

import pytest
from httpx import AsyncClient

from grabpic.main import app


@pytest.mark.asyncio
async def test_ingest_no_face():
    """Verify that images with no detectable faces return 422 Unprocessable Entity."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        files = {'file': ('test.jpg', b'\x00' * 100, 'image/jpeg')}
        response = await ac.post("/ingest", files=files)
    
    assert response.status_code == 422
    assert "No faces detected" in response.json()['detail']


@pytest.mark.asyncio
async def test_invalid_grab_id():
    """Verify that non-existent grab IDs return 404 Not Found."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        non_existent_id = "00000000-0000-0000-0000-000000000000"
        response = await ac.get(f"/images/{non_existent_id}")
    
    assert response.status_code == 404
    assert "No images found" in response.json()['detail']
