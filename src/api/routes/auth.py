"""
POST /api/v1/auth/signup

Creates a Firebase Auth user and initializes their Firestore profile.
"""

from fastapi import APIRouter, HTTPException, status
from firebase_admin import auth as firebase_auth

from src.api.firebase.client import create_user, create_user_profile
from src.api.models.requests import SignupRequest
from src.api.models.responses import SignupResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=SignupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Sign up a new user",
    description=(
        "Creates a Firebase Auth account and initialises a Firestore user profile. "
        "Returns the new user's UID and basic profile info."
    ),
)
async def signup(body: SignupRequest) -> SignupResponse:
    # 1. Create Firebase Auth user
    try:
        user_record = create_user(
            email=body.email,
            password=body.password,
            display_name=body.display_name,
        )
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create account: {exc}",
        )

    # 2. Persist profile in Firestore
    profile_data = {
        "uid": user_record.uid,
        "email": body.email,
        "display_name": body.display_name,
        "company_name": body.company_name,
        "role": body.role,
        "plan": "free",
        "simulations_run": 0,
    }
    try:
        create_user_profile(user_record.uid, profile_data)
    except Exception as exc:
        # Auth user was created; profile persistence failed — log but don't block
        # The profile can be lazily created on first login
        print(f"[WARN] Failed to create Firestore profile for {user_record.uid}: {exc}")

    return SignupResponse(
        uid=user_record.uid,
        email=body.email,
        display_name=body.display_name,
    )
