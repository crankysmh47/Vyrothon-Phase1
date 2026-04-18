from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from typing import List
import numpy as np
import cv2
from deepface import DeepFace
from .database import supabase
from .models import IngestResponse, AuthResponse, UserImagesResponse, FaceDetectionResponse, ErrorResponse
import uuid
import tempfile
import os

app = FastAPI(title="GRABPIC: Intelligent Identity & Retrieval Engine")

# Helper to process images with DeepFace
async def get_face_embeddings(image_bytes: bytes):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name
    
    try:
        # Generate 128-dim embeddings using FaceNet
        # enforce_detection=True will raise an error if no faces are found
        results = DeepFace.represent(img_path=tmp_path, model_name='Facenet', enforce_detection=True)
        return results
    except ValueError:
        raise HTTPException(status_code=422, detail="No faces detected in the provided image.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/ingest", response_model=IngestResponse, responses={422: {"model": ErrorResponse}})
async def ingest_image(file: UploadFile = File(...)):
    contents = await file.read()
    
    # 1. Detect faces and get embeddings
    embeddings_data = await get_face_embeddings(contents)
    
    # 2. Upload image to Supabase Storage (simplified for logic)
    # In a real scenario, we'd upload to a bucket and get the public URL
    image_id = uuid.uuid4()
    storage_url = f"https://supabase.storage/buckets/images/{image_id}.jpg"
    
    # 3. Store record in 'images' table
    supabase.table("images").insert({"image_id": str(image_id), "storage_url": storage_url}).execute()
    
    grab_ids = []
    for face in embeddings_data:
        grab_id = uuid.uuid4()
        embedding = face['embedding']
        
        # 4. Store in 'faces' and link in 'image_faces'
        supabase.table("faces").insert({"grab_id": str(grab_id), "embedding": embedding}).execute()
        supabase.table("image_faces").insert({"image_id": str(image_id), "grab_id": str(grab_id)}).execute()
        grab_ids.append(grab_id)
        
    return IngestResponse(image_id=image_id, faces_detected=len(grab_ids), grab_ids=grab_ids)

@app.post("/auth", response_model=AuthResponse, responses={422: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def authenticate_face(file: UploadFile = File(...)):
    contents = await file.read()
    
    # 1. Get embedding for the selfie
    embeddings_data = await get_face_embeddings(contents)
    
    if not embeddings_data:
        raise HTTPException(status_code=422, detail="No faces detected in the selfie.")
    
    # Use the first face detected in the selfie for auth
    query_embedding = embeddings_data[0]['embedding']
    
    # 2. Call Supabase RPC function 'match_face'
    response = supabase.rpc("match_face", {
        "query_embedding": query_embedding,
        "match_threshold": 0.6, # Recommended starting point
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
    
    raise HTTPException(status_code=401, detail="Selfie mismatch. No matching user found.")

@app.get("/images/{grab_id}", response_model=UserImagesResponse, responses={404: {"model": ErrorResponse}})
async def get_user_images(grab_id: uuid.UUID):
    # Join image_faces and images
    response = supabase.table("image_faces") \
        .select("images(storage_url)") \
        .filter("grab_id", "eq", str(grab_id)) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"No images found for grab_id: {grab_id}")
    
    urls = [item['images']['storage_url'] for item in response.data]
    return UserImagesResponse(grab_id=grab_id, images=urls, total_count=len(urls))
