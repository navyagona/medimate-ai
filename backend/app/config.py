import os
import logging
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

# Configure structured logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("medimate")
logger.info(f"Initialized MediMate AI (API key configured: {IS_API_KEY_VALID})")

