"""
Data models for the GRABPIC API defining request and response schemas.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, HttpUrl


class FaceDetectionResponse(BaseModel):
    """Schema for individual face detection results."""
    grab_id: UUID
    similarity: Optional[float] = None


class IngestResponse(BaseModel):
    """Schema for the image ingestion endpoint response."""
    image_id: UUID
    faces_detected: int
    grab_ids: List[UUID]


class AuthResponse(BaseModel):
    """Schema for the face authentication endpoint response."""
    authenticated: bool
    match_found: bool
    grab_id: Optional[UUID] = None
    similarity_score: Optional[float] = None
    message: str


class UserImagesResponse(BaseModel):
    """Schema for the user image retrieval endpoint response."""
    grab_id: UUID
    images: List[HttpUrl]
    total_count: int


class ErrorResponse(BaseModel):
    """Standardized error response schema."""
    detail: str
