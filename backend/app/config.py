import os
from dotenv import load_dotenv

# Load from backend/.env or root .env
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
PORT = int(os.getenv("PORT", 8000))
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

# System modes
IS_API_KEY_VALID = bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith("your_") and OPENAI_API_KEY != "dummy_key")
