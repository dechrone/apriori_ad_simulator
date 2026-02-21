"""
Apriori API Server

Starts a FastAPI application exposing three endpoint groups:

  POST /api/v1/auth/signup          - Create Firebase Auth user + Firestore profile
  POST /api/v1/assets/upload        - Upload ad-set or product-flow images to Firebase Storage
  GET  /api/v1/assets/              - List current user's uploaded assets
  POST /api/v1/simulations/run      - Run an Ad or Product-Flow simulation

Run locally:
  uvicorn app:app --reload --port 8000

Environment variables required:
  FIREBASE_SERVICE_ACCOUNT_PATH  - Path to Firebase service account JSON key
    OR
  FIREBASE_SERVICE_ACCOUNT_JSON  - Raw JSON string of the service account key
  FIREBASE_STORAGE_BUCKET        - e.g. your-project.appspot.com
  OPENROUTER_API_KEY             - Already used by simulation engine
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes.auth import router as auth_router
from src.api.routes.assets import router as assets_router
from src.api.routes.simulation import router as simulation_router


# ---------------------------------------------------------------------------
# Lifespan: warm up DB connection on startup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Do not block startup on persona DB; first request will load if needed
    yield
    # Nothing to tear down


# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Apriori Simulation API",
    version="1.0.0",
    description=(
        "AI-powered consumer simulation engine. "
        "Run ad creative or product-flow simulations against synthetic Indian personas "
        "to predict real-user reactions before launch."
    ),
    lifespan=lifespan,
)

# Allow all origins in dev; tighten to specific frontend URLs in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(assets_router, prefix=API_PREFIX)
app.include_router(simulation_router, prefix=API_PREFIX)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "apriori-api"}


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "Apriori Simulation API",
        "version": "1.0.0",
        "docs": "/docs",
    }
