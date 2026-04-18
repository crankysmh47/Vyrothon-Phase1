from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from uuid import UUID
from datetime import datetime

class FaceDetectionResponse(BaseModel):
    grab_id: UUID
    similarity: Optional[float] = None

class IngestResponse(BaseModel):
    image_id: UUID
    faces_detected: int
    grab_ids: List[UUID]

class AuthResponse(BaseModel):
    authenticated: bool
    match_found: bool
    grab_id: Optional[UUID] = None
    similarity_score: Optional[float] = None
    message: str

class UserImagesResponse(BaseModel):
    grab_id: UUID
    images: List[HttpUrl]
    total_count: int

class ErrorResponse(BaseModel):
    detail: str
