"""
POST /api/v1/assets/upload

Accepts multipart image upload(s), pushes them to Firebase Storage,
and records each URL in the authenticated user's Firestore profile.
"""

import mimetypes
import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from src.api.firebase.client import (
    append_asset_to_user,
    build_storage_path,
    get_user_assets,
    upload_file_to_storage,
)
from src.api.middleware.auth import get_current_user
from src.api.models.responses import AssetUploadResponse

router = APIRouter(prefix="/assets", tags=["Assets"])

# Maximum individual file size: 20 MB
MAX_FILE_BYTES = 20 * 1024 * 1024

ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
}


def _asset_type_label(asset_type_int: int) -> str:
    return "adset" if asset_type_int == 0 else "product_flow"


@router.post(
    "/upload",
    response_model=List[AssetUploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload ad-set or product-flow images",
    description=(
        "Upload one or more images via multipart/form-data.\n\n"
        "- `type`: **0** = Ad-set image, **1** = Product flow screen\n"
        "- `images`: one or more image files\n\n"
        "Each file is stored in Firebase Storage under the authenticated user's namespace. "
        "The resulting URLs are persisted to the user's Firestore profile and returned."
    ),
)
async def upload_assets(
    type: Annotated[int, Form(description="0 = Ad-set, 1 = Product flow")] = 0,
    images: List[UploadFile] = File(..., description="Image file(s) to upload"),
    current_user: dict = Depends(get_current_user),
) -> List[AssetUploadResponse]:
    if type not in (0, 1):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="`type` must be 0 (Ad-set) or 1 (Product flow).",
        )

    asset_type = _asset_type_label(type)
    uid = current_user["uid"]
    results: List[AssetUploadResponse] = []

    for upload in images:
        # --- Validate content type ---
        content_type = upload.content_type or "application/octet-stream"
        if content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{content_type}' for '{upload.filename}'. "
                       f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}",
            )

        # --- Read bytes and enforce size limit ---
        file_bytes = await upload.read()
        if len(file_bytes) > MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File '{upload.filename}' exceeds the 20 MB limit.",
            )

        # --- Upload to Firebase Storage ---
        filename = upload.filename or f"{uuid.uuid4().hex}.jpg"
        storage_path = build_storage_path(uid, asset_type, filename)
        try:
            public_url = upload_file_to_storage(file_bytes, storage_path, content_type)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Storage upload failed for '{filename}': {exc}",
            )

        # --- Persist URL to Firestore user profile ---
        asset_id = uuid.uuid4().hex
        metadata = {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": len(file_bytes),
            "storage_path": storage_path,
        }
        try:
            append_asset_to_user(uid, asset_type, public_url, metadata)
        except Exception as exc:
            # Non-fatal: URL is already in Storage; just log
            print(f"[WARN] Could not persist asset metadata for uid={uid}: {exc}")

        results.append(
            AssetUploadResponse(
                asset_id=asset_id,
                url=public_url,
                asset_type=asset_type,
                filename=filename,
            )
        )

    return results


@router.get(
    "/",
    summary="List uploaded assets for the current user",
    description="Returns all uploaded assets for the authenticated user. "
                "Pass `?type=0` for ad-sets or `?type=1` for product flows.",
)
async def list_assets(
    type: int | None = None,
    current_user: dict = Depends(get_current_user),
):
    uid = current_user["uid"]
    asset_type = _asset_type_label(type) if type is not None else None
    return get_user_assets(uid, asset_type=asset_type)
