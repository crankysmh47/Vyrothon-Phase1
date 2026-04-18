# GRABPIC: Intelligent Identity and Retrieval Engine

GRABPIC is a high-performance biometric identification and image retrieval system. It utilizes the FaceNet model for facial feature extraction and leveraging the pgvector extension within Supabase for efficient vector similarity searches using HNSW indexing.

## Architecture and Engineering Decisions

### Postgres RPC for Vector Mathematics
The system utilizes a PostgreSQL Stored Procedure (`match_face` RPC) to execute cosine similarity calculations directly within the database layer. This architectural choice minimizes network latency by avoiding the transfer of large vector payloads and leverages the native binary execution speed of the PostgreSQL engine.

### Event-Loop Concurrency Safety
The FastAPI endpoints are implemented using standard `def` instead of `async def`. Given that the DeepFace inference engine and the Supabase-py client are synchronous and blocking operations, executing them within an asynchronous context would stall the ASGI event loop. By utilizing standard definitions, FastAPI automatically delegates these tasks to an external thread pool, ensuring the server remains responsive to concurrent requests.

### Ingestion Deduplication
The `/ingest` endpoint executes a biometric identity check against existing records prior to insertion. If a detected face matches an existing identity within the defined similarity threshold (0.5), the system reuses the existing `grab_id`. This implementation ensures that multiple photographs containing the same individual are unified under a single biometric key.

## Technical Specifications

- **Backend Framework**: FastAPI
- **Machine Learning**: DeepFace (FaceNet)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Search Algorithm**: HNSW (Hierarchical Navigable Small World)
- **Vector Dimension**: 128

## Initial Setup SOP

### 1. Environment Configuration
Establish a Python virtual environment and install the necessary dependencies:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database Initialization
Execute the `setup.sql` script within the Supabase SQL Editor to initialize the necessary extensions, tables, and RPC functions.

### 3. Environment Variables
Configure a `.env` file in the root directory with the following credentials:

```env
SUPABASE_URL=your_project_url
SUPABASE_KEY=your_service_role_key
```

### 4. Pre-Flight: Download Model Weights
Execute the following command to pre-cache the FaceNet weights and prevent initialization latency during the first API request:

```powershell
python -c "from deepface import DeepFace; DeepFace.represent('grabpic/test_images/ben.jpeg', model_name='Facenet', enforce_detection=False)"
```

### 5. Application Execution
Start the server using Uvicorn:

```powershell
uvicorn grabpic.main:app --reload
```

## API Documentation

- `POST /ingest`: Processes an image to detect faces and register them in the persistent storage.
- `POST /auth`: Performs biometric authentication via selfie matching.
- `GET /images/{grab_id}`: Retrieves all storage URLs associated with a specific biometric identity.
