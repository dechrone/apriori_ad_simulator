"""
Firebase Admin SDK client - single shared instance for Auth, Firestore, and Storage.

Initialization (in order of precedence):
  - FIREBASE_SERVICE_ACCOUNT_PATH env (or from config: default backend/firebase-credentials.json)
  - FIREBASE_SERVICE_ACCOUNT_JSON env (raw JSON string)
  - Application Default Credentials (GCP/Cloud Run)
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import firebase_admin
from firebase_admin import auth, credentials, firestore, storage


def _resolve_firebase_credentials():
    """Resolve credential: path (from env or default firebase-credentials.json), or JSON string, or ADC."""
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if sa_json:
        return credentials.Certificate(json.loads(sa_json)), None

    # Prefer env path, then config default (backend/firebase-credentials.json)
    from src.utils.config import FIREBASE_SERVICE_ACCOUNT_PATH, BASE_DIR
    sa_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH") or FIREBASE_SERVICE_ACCOUNT_PATH
    path = Path(sa_path)
    if not path.is_absolute():
        path = BASE_DIR / path
    if path.exists():
        return credentials.Certificate(str(path)), path
    # Fallback: Application Default Credentials
    return credentials.ApplicationDefault(), None


def _get_storage_bucket():
    """Storage bucket from env, or project_id.appspot.com from credential file if available."""
    bucket = os.getenv("FIREBASE_STORAGE_BUCKET", "").strip()
    if bucket:
        return bucket
    from src.utils.config import FIREBASE_STORAGE_BUCKET
    if FIREBASE_STORAGE_BUCKET:
        return FIREBASE_STORAGE_BUCKET
    # If we used a credential file, we can read project_id from it
    from src.utils.config import FIREBASE_SERVICE_ACCOUNT_PATH, BASE_DIR
    path = Path(os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH") or FIREBASE_SERVICE_ACCOUNT_PATH)
    if not path.is_absolute():
        path = BASE_DIR / path
    if path.exists():
        try:
            data = json.loads(path.read_text())
            return data.get("project_id", "") + ".appspot.com"
        except Exception:
            pass
    return ""


def _initialize_app() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK. Idempotent.
    Uses firebase-credentials.json (or FIREBASE_SERVICE_ACCOUNT_PATH / FIREBASE_SERVICE_ACCOUNT_JSON).
    """
    if firebase_admin._DEFAULT_APP_NAME in firebase_admin._apps:
        return firebase_admin.get_app()

    cred, _ = _resolve_firebase_credentials()
    bucket = _get_storage_bucket()
    return firebase_admin.initialize_app(cred, {"storageBucket": bucket})


def _get_app() -> firebase_admin.App:
    """Lazy init: called on first actual use, not on module import."""
    return _initialize_app()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def create_user(email: str, password: str, display_name: Optional[str] = None) -> auth.UserRecord:
    """Create a new Firebase Auth user and return the UserRecord."""
    _get_app()
    kwargs: Dict[str, Any] = {"email": email, "password": password}
    if display_name:
        kwargs["display_name"] = display_name
    return auth.create_user(**kwargs)


def verify_id_token(id_token: str) -> Dict[str, Any]:
    """
    Verify a Firebase ID token (from client SDK) and return decoded claims.
    Raises firebase_admin.auth.InvalidIdTokenError on failure.
    """
    _get_app()
    return auth.verify_id_token(id_token)


# ---------------------------------------------------------------------------
# Firestore helpers
# ---------------------------------------------------------------------------

def get_db():
    """Return the Firestore client (lazy singleton)."""
    _get_app()
    return firestore.client()


def create_user_profile(uid: str, data: Dict[str, Any]) -> None:
    """Create or overwrite a user document in the `users` collection."""
    db = get_db()
    db.collection("users").document(uid).set(
        {
            **data,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }
    )


def get_user_profile(uid: str) -> Optional[Dict[str, Any]]:
    """Fetch a user document. Returns None if it doesn't exist."""
    db = get_db()
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None


def update_user_profile(uid: str, data: Dict[str, Any]) -> None:
    """Merge-update a user document (creates if missing)."""
    db = get_db()
    db.collection("users").document(uid).set(
        {**data, "updated_at": datetime.utcnow().isoformat()},
        merge=True,
    )


def append_asset_to_user(uid: str, asset_type: str, url: str, metadata: Dict[str, Any]) -> None:
    """
    Append an uploaded asset URL to the user's `assets` sub-collection.

    asset_type: "adset" | "product_flow"
    """
    db = get_db()
    db.collection("users").document(uid).collection("assets").add(
        {
            "asset_type": asset_type,
            "url": url,
            "metadata": metadata,
            "uploaded_at": datetime.utcnow().isoformat(),
        }
    )


def _firestore_where(ref, field: str, op: str, value: Any):
    """Apply .where() using filter=FieldFilter to avoid positional-argument warning."""
    try:
        from google.cloud.firestore_v1.base_query import FieldFilter
        return ref.where(filter=FieldFilter(field, op, value))
    except ImportError:
        return ref.where(field, op, value)


def get_user_assets(uid: str, asset_type: Optional[str] = None) -> list:
    """Return a user's uploaded assets, optionally filtered by type."""
    db = get_db()
    ref = db.collection("users").document(uid).collection("assets")
    if asset_type:
        ref = _firestore_where(ref, "asset_type", "==", asset_type)
    return [{"id": doc.id, **doc.to_dict()} for doc in ref.stream()]


# ---------------------------------------------------------------------------
# Apriori users (Clerk profile) – apriori_users collection
# ---------------------------------------------------------------------------

def _users_collection():
    from src.utils.config import FIRESTORE_USERS_COLLECTION
    return get_db().collection(FIRESTORE_USERS_COLLECTION)


def get_user_by_clerk_id(profile_id: str) -> Optional[Tuple[str, Dict[str, Any]]]:
    """
    Find user profile by clerkId (profileId from frontend).
    Returns (document_id, document_data) or None if not found.
    """
    ref = _firestore_where(_users_collection(), "clerkId", "==", profile_id).limit(1)
    docs = list(ref.stream())
    if not docs:
        return None
    doc = docs[0]
    return (doc.id, doc.to_dict() or {})


def get_audience_by_id(user_doc_id: str, audience_id: str) -> Optional[Dict[str, Any]]:
    """
    Get audience document by id from user's audiences subcollection.
    Audience doc typically has: name, description (used as target user descriptor).
    """
    doc = _users_collection().document(user_doc_id).collection("audiences").document(audience_id).get()
    return doc.to_dict() if doc.exists else None


def get_asset_folder(user_doc_id: str, folder_id: str) -> Optional[Dict[str, Any]]:
    """Get asset folder document by folder_id. Has assetType, name, assets subcollection."""
    doc = _users_collection().document(user_doc_id).collection("assetFolders").document(folder_id).get()
    return doc.to_dict() if doc.exists else None


def get_folder_assets(user_doc_id: str, folder_id: str) -> List[Dict[str, Any]]:
    """
    Get all assets in an asset folder, each with url and stepNumber.
    Returns list sorted by stepNumber (ascending). Missing stepNumber treated as 0.
    """
    ref = (
        _users_collection()
        .document(user_doc_id)
        .collection("assetFolders")
        .document(folder_id)
        .collection("assets")
    )
    assets = [{"id": d.id, **d.to_dict()} for d in ref.stream()]
    for a in assets:
        if "stepNumber" not in a or a["stepNumber"] is None:
            a["stepNumber"] = 0
    assets.sort(key=lambda a: (a["stepNumber"], a.get("id", "")))
    return assets


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------

def upload_file_to_storage(
    file_bytes: bytes,
    destination_path: str,
    content_type: str = "image/jpeg",
) -> str:
    """
    Upload raw bytes to Firebase Storage and return a public download URL.

    destination_path: e.g. "users/{uid}/adsets/image.jpg"
    """
    _get_app()
    bucket = storage.bucket()
    blob = bucket.blob(destination_path)
    blob.upload_from_string(file_bytes, content_type=content_type)
    blob.make_public()
    return blob.public_url


def build_storage_path(uid: str, asset_type: str, filename: str) -> str:
    """Build a deterministic, unique GCS path for an uploaded asset."""
    unique_id = uuid.uuid4().hex[:8]
    folder = "adsets" if asset_type == "adset" else "product_flows"
    return f"users/{uid}/{folder}/{unique_id}_{filename}"
