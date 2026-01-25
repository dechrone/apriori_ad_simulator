"""Configuration management for Apriori."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project Paths
BASE_DIR = Path(__file__).parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# API Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Model Configuration (OpenRouter model IDs)
GEMINI_PRO_MODEL = os.getenv("GEMINI_PRO_MODEL", "google/gemini-2.5-pro")
GEMINI_FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "google/gemini-2.5-flash")

# Simulation Configuration
TIER1_SAMPLE_SIZE = int(os.getenv("TIER1_SAMPLE_SIZE", "100"))
TIER2_SAMPLE_SIZE = int(os.getenv("TIER2_SAMPLE_SIZE", "900"))
MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "50"))

# DuckDB Configuration
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "apriori.db"))

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
