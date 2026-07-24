import pytest
import numpy as np
from app.services.rag import get_fallback_embedding, cosine_similarity, retrieve_guidelines

def test_fallback_embedding_dimensions_and_normalization():
    """Verify fallback embedding output is 1536-dimensional and L2-normalized."""
    embedding = get_fallback_embedding("Hypertension stage 2 patient taking lisinopril")
    assert len(embedding) == 1536
    norm = np.linalg.norm(embedding)
    assert pytest.approx(norm, abs=1e-5) == 1.0

def test_cosine_similarity_identity_and_orthogonality():
    """Verify vector similarity math for identical and zero vectors."""
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    v3 = [0.0, 1.0, 0.0]
    
    assert pytest.approx(cosine_similarity(v1, v2), abs=1e-5) == 1.0
    assert pytest.approx(cosine_similarity(v1, v3), abs=1e-5) == 0.0
    assert cosine_similarity(v1, [0.0, 0.0, 0.0]) == 0.0

def test_retrieve_guidelines_hypertension_query():
    """Verify RAG retrieval fetches relevant clinical guideline objects for hypertension."""
    results = retrieve_guidelines("blood pressure 145 over 92 headache hypertension", limit=2)
    assert isinstance(results, list)
    assert len(results) > 0
    first = results[0]
    assert "id" in first
    assert "condition" in first
    assert "content" in first

def test_retrieve_guidelines_asthma_query():
    """Verify RAG retrieval fetches relevant asthma guideline snippets."""
    results = retrieve_guidelines("wheezing shortness of breath inhaler albuterol asthma", limit=2)
    assert len(results) > 0
    conditions = [r["condition"] for r in results]
    assert any("Asthma" in c for c in conditions)
