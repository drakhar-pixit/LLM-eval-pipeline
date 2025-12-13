from fastapi import FastAPI
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from typing import List, Dict, Any

app = FastAPI(title="Vector Encoder Service", version="1.0.0")

# Global encoder instance
encoder = None

class VectorSelectionRequest(BaseModel):
    user_query: str
    vectors: List[Dict[str, Any]]

class VectorSelectionResponse(BaseModel):
    selected_vector: Dict[str, Any]
    similarity_score: float

@app.on_event("startup")
async def startup_event():
    global encoder
    print("Loading sentence transformer model...")
    encoder = SentenceTransformer('all-MiniLM-L6-v2')
    print("Vector Encoder Service ready!")

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.post("/select-vector", response_model=VectorSelectionResponse)
async def select_most_relevant_vector(request: VectorSelectionRequest):
    """Select the most relevant vector based on cosine similarity with user query"""
    
    if not request.vectors:
        return VectorSelectionResponse(
            selected_vector={},
            similarity_score=0.0
        )
    
    if len(request.vectors) == 1:
        return VectorSelectionResponse(
            selected_vector=request.vectors[0],
            similarity_score=1.0
        )
    
    # Encode user query
    query_embedding = encoder.encode([request.user_query])
    
    # MaxSim: chunk long texts and take max similarity
    max_scores = []
    for vector in request.vectors:
        text = vector.get('text', '')
        words = text.split()
        
        # Chunk into ~100 word segments
        chunk_size = 100
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
        
        if not chunks:
            max_scores.append(0.0)
            continue
        
        # Encode all chunks
        chunk_embeddings = encoder.encode(chunks)
        
        # Get max similarity across all chunks
        chunk_sims = cosine_similarity(query_embedding, chunk_embeddings)[0]
        max_scores.append(float(np.max(chunk_sims)))
    
    max_scores = np.array(max_scores)
    
    # Log all similarity scores
    print(f"\nQuery: {request.user_query[:100]}...")
    for vec, score in zip(request.vectors, max_scores):
        print(f"  Vector {vec.get('id')}: MaxSim={score:.4f}")
    
    # Find most similar vector
    most_similar_idx = np.argmax(max_scores)
    print(f"Selected: Vector {request.vectors[most_similar_idx].get('id')} with MaxSim {max_scores[most_similar_idx]:.4f}\n")
    
    return VectorSelectionResponse(
        selected_vector=request.vectors[most_similar_idx],
        similarity_score=float(max_scores[most_similar_idx])
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)