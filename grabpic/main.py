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
def get_face_embeddings(image_bytes: bytes):
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
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid or unreadable image file: {str(e)}")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/ingest", response_model=IngestResponse, responses={422: {"model": ErrorResponse}})
def ingest_image(file: UploadFile = File(...)):
    contents = file.file.read()
    
    # 1. Detect faces and get embeddings
    embeddings_data = get_face_embeddings(contents)
    
    image_id = str(uuid.uuid4())
    storage_url = f"https://supabase.storage/buckets/images/{image_id}.jpg"
    
    # 2. Store record in 'images' table
    supabase.table("images").insert({"image_id": image_id, "storage_url": storage_url}).execute()
    
    # Use a set to prevent primary key crashes if the same face is detected twice in one photo
    unique_grab_ids_in_image = set() 
    
    for face in embeddings_data:
        embedding = face['embedding']
        
        # 3. IDENTIFY: Does this face already exist in our database?
        match_response = supabase.rpc("match_face", {
            "query_embedding": embedding,
            "match_threshold": 0.5, # Use the same threshold as auth
            "match_count": 1
        }).execute()
        
        if match_response.data:
            # Existing person! Reuse their grab_id
            grab_id = match_response.data[0]['grab_id']
        else:
            # Brand new person! Create a new grab_id
            grab_id = str(uuid.uuid4())
            supabase.table("faces").insert({"grab_id": grab_id, "embedding": embedding}).execute()
        
        # 4. LINK: Map the image to the grab_id (only once per person per image)
        if grab_id not in unique_grab_ids_in_image:
            supabase.table("image_faces").insert({"image_id": image_id, "grab_id": grab_id}).execute()
            unique_grab_ids_in_image.add(grab_id)
            
    return IngestResponse(
        image_id=uuid.UUID(image_id), 
        faces_detected=len(unique_grab_ids_in_image), 
        grab_ids=[uuid.UUID(gid) for gid in unique_grab_ids_in_image]
    )
    
@app.post("/auth", response_model=AuthResponse, responses={422: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
def authenticate_face(file: UploadFile = File(...)):
    contents = file.file.read()
    
    # 1. Get embedding for the selfie
    embeddings_data = get_face_embeddings(contents)
    
    # Use the first face detected in the selfie for auth
    query_embedding = embeddings_data[0]['embedding']
    
    # 2. Call Supabase RPC function 'match_face'
    response = supabase.rpc("match_face", {
        "query_embedding": query_embedding,
        "match_threshold": 0.5, # Lowered from 0.6 for better matching
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
    
    # Optional debugging: get the best non-matching score for guidance
    best_match = supabase.rpc("match_face", {
        "query_embedding": query_embedding,
        "match_threshold": 0.0, # Get the absolute best possible match
        "match_count": 1
    }).execute()
    
    score_hint = f" Best score seen: {best_match.data[0]['similarity']:.4f}" if best_match.data else ""
    raise HTTPException(status_code=401, detail=f"Selfie mismatch. No matching user found. {score_hint}")

@app.get("/images/{grab_id}", response_model=UserImagesResponse, responses={404: {"model": ErrorResponse}})
def get_user_images(grab_id: uuid.UUID):
    # Join image_faces and images
    response = supabase.table("image_faces") \
        .select("images(storage_url)") \
        .filter("grab_id", "eq", str(grab_id)) \
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=404, detail=f"No images found for grab_id: {grab_id}")
    
    urls = [item['images']['storage_url'] for item in response.data if item.get('images')]
    return UserImagesResponse(grab_id=grab_id, images=urls, total_count=len(urls))
