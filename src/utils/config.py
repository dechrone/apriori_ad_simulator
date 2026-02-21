"""Configuration management for Apriori."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Project Paths (before load_dotenv so BASE_DIR is available for .env.local path)
BASE_DIR = Path(__file__).parent.parent.parent

# Load environment variables: .env first, then .env.local (local overrides)
load_dotenv(BASE_DIR / ".env")
load_dotenv(BASE_DIR / ".env.local")
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Configuration (OpenRouter model IDs)
# Using Claude for Pro tasks (vision capable) and GPT-3.5 for Flash tasks (fast/cheap)
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "anthropic/claude-3.5-sonnet")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "openai/gpt-3.5-turbo")

# Simulation Configuration
TIER1_SAMPLE_SIZE = int(os.getenv("TIER1_SAMPLE_SIZE", "100"))
TIER2_SAMPLE_SIZE = int(os.getenv("TIER2_SAMPLE_SIZE", "900"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))

# DuckDB Configuration
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "apriori.db"))

# Firestore (frontend / Clerk integration)
FIRESTORE_USERS_COLLECTION = os.getenv("FIRESTORE_USERS_COLLECTION", "apriori_users")

# Firebase (optional: path to service account JSON; default backend/firebase-credentials.json)
FIREBASE_SERVICE_ACCOUNT_PATH = os.getenv(
    "FIREBASE_SERVICE_ACCOUNT_PATH",
    str(BASE_DIR / "firebase-credentials.json"),
)
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "")

# Cloudinary (optional: for signed URLs or API if asset URLs need auth)
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")

# Model Generation Parameters
GENERATION_CONFIG = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}

# Validation Thresholds
TRUST_SCORE_THRESHOLD = 3
MIN_LITERACY_FOR_COMPLEX_FORM = 5
