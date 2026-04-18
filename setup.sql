-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create images table
CREATE TABLE IF NOT EXISTS images (
    image_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    storage_url TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 3. Create faces table (128-dim for FaceNet)
CREATE TABLE IF NOT EXISTS faces (
    grab_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    embedding VECTOR(128)
);

-- 4. Create junction table
CREATE TABLE IF NOT EXISTS image_faces (
    image_id UUID REFERENCES images(image_id) ON DELETE CASCADE,
    grab_id UUID REFERENCES faces(grab_id) ON DELETE CASCADE,
    PRIMARY KEY (image_id, grab_id)
);

-- 5. Create HNSW Index for near-instant similarity search
CREATE INDEX IF NOT EXISTS faces_embedding_hnsw_idx 
ON faces USING hnsw (embedding vector_cosine_ops);

-- 6. Create RPC function for face matching
CREATE OR REPLACE FUNCTION match_face(
    query_embedding VECTOR(128),
    match_threshold FLOAT,
    match_count INT
)
RETURNS TABLE (grab_id UUID, similarity FLOAT)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT f.grab_id,
         1 - (f.embedding <=> query_embedding) AS similarity
  FROM   faces f
  WHERE  1 - (f.embedding <=> query_embedding) > match_threshold
  ORDER  BY similarity DESC
  LIMIT  match_count;
END;
$$;
