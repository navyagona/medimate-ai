import os
import sys
import json
import logging
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

# Add backend directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import QDRANT_HOST, QDRANT_PORT
from app.services.rag import get_embedding, GUIDELINES_RAW_PATH, GUIDELINES_VECTOR_PATH

logger = logging.getLogger(__name__)

def run_ingestion():
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception as e:
        logger.debug(f"stdout encoding reconfiguration ignored: {e}")

    logger.info("=== MediMate Clinical Guidelines Ingestion System ===")
    
    # 1. Read raw guidelines
    if not os.path.exists(GUIDELINES_RAW_PATH):
        logger.error(f"Raw guidelines not found at: {GUIDELINES_RAW_PATH}")
        sys.exit(1)
        
    with open(GUIDELINES_RAW_PATH, "r", encoding="utf-8") as f:
        guidelines = json.load(f)
        
    logger.info(f"Loaded {len(guidelines)} guideline chunks. Processing embeddings...")
    
    vectorized_db = []
    points = []
    
    for i, chunk in enumerate(guidelines):
        logger.info(f"[{i+1}/{len(guidelines)}] Embedding: {chunk['id']} - {chunk['title']}")
        embedding_text = f"Condition: {chunk['condition']}\nCategory: {chunk['category']}\nTitle: {chunk['title']}\nContent: {chunk['content']}"
        
        # Embed
        vector = get_embedding(embedding_text)
        
        # Add to local offline vector cache database
        vectorized_db.append({
            **chunk,
            "embedding": vector
        })
        
        # Prepare Qdrant Point
        points.append(PointStruct(
            id=i,
            vector=vector,
            payload=chunk
        ))
        
    # Ensure backend/data directory exists
    os.makedirs(os.path.dirname(GUIDELINES_VECTOR_PATH), exist_ok=True)
    
    # Save local vector file (fallback RAG)
    with open(GUIDELINES_VECTOR_PATH, "w", encoding="utf-8") as f:
        json.dump(vectorized_db, f, indent=2, ensure_ascii=False)
    logger.info(f"Local fallback vector DB cached successfully at: {GUIDELINES_VECTOR_PATH}")
    
    # 2. Try pushing to Qdrant container
    logger.info(f"Connecting to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}...")
    try:
        q_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=3.0)
        
        # Recreate collection
        q_client.recreate_collection(
            collection_name="guidelines",
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
        )
        
        # Upload
        q_client.upsert(
            collection_name="guidelines",
            points=points
        )
        logger.info("Successfully uploaded vector collections to Qdrant Docker Database!")
    except Exception as e:
        logger.warning(f"Qdrant connection failed ({e}). Ingestion completed in local fallback vector file.")
        logger.info("Note: The application will run successfully using the offline local vector database.")
        
    logger.info("=== Ingestion Finished ===")

if __name__ == "__main__":
    run_ingestion()

