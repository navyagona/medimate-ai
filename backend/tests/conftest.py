import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure backend and project root are in sys.path for test execution
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.main import app

@pytest.fixture
def client():
    """Provides a FastAPI TestClient instance for API integration testing."""
    with TestClient(app) as test_client:
        yield test_client
