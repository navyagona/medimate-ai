import os
import json
import hashlib
import logging
import numpy as np
from openai import OpenAI
from qdrant_client import QdrantClient
from app.config import OPENAI_API_KEY, QDRANT_HOST, QDRANT_PORT, IS_API_KEY_VALID

logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
GUIDELINES_RAW_PATH = os.path.join(BASE_DIR, "backend", "ingestion", "clinical_guidelines.json")
GUIDELINES_VECTOR_PATH = os.path.join(BASE_DIR, "backend", "data", "guidelines_vector_db.json")

openai_client = OpenAI(api_key=OPENAI_API_KEY if IS_API_KEY_VALID else "dummy_key", max_retries=0)

# Global status tracking to avoid repeating connection timeouts if Qdrant container is offline
_qdrant_offline = False

# Global API quota status shared between RAG and LLM agent processes
_api_quota_exceeded = False

def get_fallback_embedding(text: str) -> list:
    """Generate offline 1536-dim text-hashing vector."""
    vector = np.zeros(1536)
    # Basic normalization and tokenization
    clean_text = text.lower()
    for char in [',', '.', '!', '?', ';', ':', '-', '_', '(', ')']:
        clean_text = clean_text.replace(char, ' ')
    words = [w for w in clean_text.split() if len(w) > 2]
    
    for word in words:
        # MD5 hash to 128-bit int, then modulo 1536
        h = int(hashlib.md5(word.encode('utf-8')).hexdigest(), 16)
        index = h % 1536
        vector[index] += 1.0
        
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()

def get_embedding(text: str) -> list:
    """Gets OpenAI embeddings, or falls back to local text hashing."""
    global _api_quota_exceeded
    if not IS_API_KEY_VALID or _api_quota_exceeded:
        return get_fallback_embedding(text)
        
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        error_msg = str(e).lower()
        if "quota" in error_msg or "limit" in error_msg or "429" in error_msg or "billing" in error_msg:
            logger.warning("OpenAI quota limit detected. Dynamic failover to offline embeddings activated.")
            _api_quota_exceeded = True
        else:
            logger.warning(f"OpenAI embedding failed: {e}. Using local fallback.")
        return get_fallback_embedding(text)

def cosine_similarity(v1, v2) -> float:
    dot = np.dot(v1, v2)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    return float(dot / (n1 * n2))

def retrieve_guidelines(query_text: str, limit: int = 3) -> list:
    """Retrieves relevant guidelines from Qdrant, falling back to local search if Qdrant is offline."""
    query_vector = get_embedding(query_text)
    
    global _qdrant_offline
    
    # 1. Try Qdrant (only if not confirmed offline)
    if not _qdrant_offline:
        try:
            q_client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=2.0)
            # Check if collection exists
            collections = q_client.get_collections().collections
            has_guidelines = any(c.name == "guidelines" for c in collections)
            
            if has_guidelines:
                results = q_client.search(
                    collection_name="guidelines",
                    query_vector=query_vector,
                    limit=limit
                )
                retrieved = []
                for hit in results:
                    payload = hit.payload
                    retrieved.append({
                        "id": payload.get("id"),
                        "condition": payload.get("condition"),
                        "category": payload.get("category"),
                        "title": payload.get("title"),
                        "content": payload.get("content"),
                        "score": hit.score
                    })
                logger.info("Guidelines retrieved via local Qdrant Vector DB.")
                return retrieved
        except Exception as e:
            # Fallback to local file-based database if Qdrant fails
            logger.warning(f"Qdrant unreachable. Dynamic failover to local search activated. Error: {e}")
            _qdrant_offline = True
        
    # 2. Try Local Vector DB File
    if os.path.exists(GUIDELINES_VECTOR_PATH):
        with open(GUIDELINES_VECTOR_PATH, "r", encoding="utf-8") as f:
            local_db = json.load(f)
            
        scored = []
        for item in local_db:
            score = cosine_similarity(query_vector, item["embedding"])
            scored.append({
                "id": item["id"],
                "condition": item["condition"],
                "category": item["category"],
                "title": item["title"],
                "content": item["content"],
                "score": score
            })
            
        # Sort descending and return top limit
        scored.sort(key=lambda x: x["score"], reverse=True)
        logger.info(f"Retrieved top {len(scored[:limit])} guidelines via local vector file fallback.")
        return scored[:limit]
        
    # 3. Last fallback: direct raw keywords search if no vector file exists
    logger.warning("Vector DB file not found. Falling back to simple keyword matching.")
    if os.path.exists(GUIDELINES_RAW_PATH):
        with open(GUIDELINES_RAW_PATH, "r", encoding="utf-8") as f:
            raw_guidelines = json.load(f)
            
        scored = []
        q_words = set(query_text.lower().split())
        for item in raw_guidelines:
            text_pool = f"{item['condition']} {item['category']} {item['title']} {item['content']}".lower()
            overlap = sum(1 for w in q_words if w in text_pool)
            score = overlap / max(len(q_words), 1)
            scored.append({
                **item,
                "score": score
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:limit]
        
    return []

