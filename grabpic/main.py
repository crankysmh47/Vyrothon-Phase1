"""
Main application module for the GRABPIC API.
Implements endpoints for biometric ingestion, authentication, and image retrieval.
"""

import os
import tempfile
import uuid
from typing import List

from deepface import DeepFace
from fastapi import FastAPI, File, HTTPException, UploadFile

# Internal module imports
from .database import supabase
from .models import (
    AuthResponse,
    ErrorResponse,
    IngestResponse,
    UserImagesResponse,
)

app = FastAPI(title="GRABPIC: Intelligent Identity & Retrieval Engine")


def get_face_embeddings(image_bytes: bytes) -> List[dict]:
    """
    Extract facial embeddings from raw image bytes using the FaceNet model.

    Args:
        image_bytes: The raw bytes of the image to process.

    Returns:
        List[dict]: A list of dictionaries containing face embeddings and metadata.

    Raises:
        HTTPException: 422 error if no faces are detected or if the file is invalid.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    
    try:
        results = DeepFace.represent(
            img_path=tmp_path, 
            model_name='Facenet', 
            enforce_detection=True
        )
        return results
    except ValueError:
        raise HTTPException(
            status_code=422, 
            detail="No faces detected in the provided image."
        )
    except Exception as e:
        raise HTTPException(
            status_code=422, 
            detail=f"Invalid or unreadable image file: {str(e)}"
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/ingest", response_model=IngestResponse, responses={422: {"model": ErrorResponse}})
def ingest_image(file: UploadFile = File(...)) -> IngestResponse:
    """
    Ingest an image, detect faces, and link them to unique or existing identities.

    Args:
        file: The image file to ingest.

    Returns:
        IngestResponse: Object containing the image ID and the associated grab IDs.
    """
    contents = file.file.read()
    embeddings_data = get_face_embeddings(contents)
    
    image_id = str(uuid.uuid4())
    storage_url = f"https://supabase.storage/buckets/images/{image_id}.jpg"
    
    # Register image record in persistence layer
    supabase.table("images").insert({"image_id": image_id, "storage_url": storage_url}).execute()
    
    unique_grab_ids_in_image = set() 
    
    for face in embeddings_data:
        embedding = face['embedding']
        
        # Identity identification via vector similarity search
        match_response = supabase.rpc("match_face", {
            "query_embedding": embedding,
            "match_threshold": 0.5,
            "match_count": 1
        }).execute()
        
        if match_response.data:
            grab_id = match_response.data[0]['grab_id']
        else:
            grab_id = str(uuid.uuid4())
            supabase.table("faces").insert({"grab_id": grab_id, "embedding": embedding}).execute()
        
        # Link image to identity in junction table
        if grab_id not in unique_grab_ids_in_image:
            supabase.table("image_faces").insert({"image_id": image_id, "grab_id": grab_id}).execute()
            unique_grab_ids_in_image.add(grab_id)
            
    return IngestResponse(
        image_id=uuid.UUID(image_id), 
        faces_detected=len(unique_grab_ids_in_image), 
        grab_ids=[uuid.UUID(gid) for gid in unique_grab_ids_in_image]
    )


@app.post("/auth", response_model=AuthResponse, responses={422: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
def authenticate_face(file: UploadFile = File(...)) -> AuthResponse:
    """
    Perform biometric authentication by matching a selfie against the database.

    Args:
        file: The selfie image for authentication.

    Returns:
        AuthResponse: Status of authentication and similarity metrics.
    """
    contents = file.file.read()
    embeddings_data = get_face_embeddings(contents)
    query_embedding = embeddings_data[0]['embedding']
    
    # Execute vector similarity RPC
    response = supabase.rpc("match_face", {
        "query_embedding": query_embedding,
        "match_threshold": 0.5,
        "match_count": 1
    }).execute()
    
    if response.data:
        match = response.data[0]
        return AuthResponse(
            authenticated=True,
            match_found=True,
            grab_id=match['grab_id'],
            similarity_score=match['similarity'],
            message="Authentication successful."
        )
    
    # Best-match retrieval for scoring diagnostics
    best_match = supabase.rpc("match_face", {
        "query_embedding": query_embedding,
        "match_threshold": 0.0,
        "match_count": 1
    }).execute()
    
    score_hint = f" Best score seen: {best_match.data[0]['similarity']:.4f}" if best_match.data else ""
    raise HTTPException(
        status_code=401, 
        detail=f"Selfie mismatch. No matching user found.{score_hint}"
    )


@app.get("/images/{grab_id}", response_model=UserImagesResponse, responses={404: {"model": ErrorResponse}})
def get_user_images(grab_id: uuid.UUID) -> UserImagesResponse:
    """
    Retrieve all image storage URLs associated with a specific grab_id.

    Args:
        grab_id: The unique biometric ID of the user.

    Returns:
        UserImagesResponse: List of storage URLs and metadata.
    """
    response = supabase.table("image_faces") \
        .select("images(storage_url)") \
        .filter("grab_id", "eq", str(grab_id)) \
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=404, 
            detail=f"No images found for grab_id: {grab_id}"
        )
    
    urls = [item['images']['storage_url'] for item in response.data if item.get('images')]
    return UserImagesResponse(grab_id=grab_id, images=urls, total_count=len(urls))
