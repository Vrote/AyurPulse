from datetime import datetime, timezone
from bson import ObjectId

from app.auth.password_handler import hash_password, verify_password
from app.auth.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
)
from app.config.settings import settings
from app.db.mongodb import get_db
from app.schemas.auth_schema import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    UserResponse,
    RegisterResponse,
    MessageResponse,
)


def _format_user(user: dict) -> UserResponse:
    """Convert MongoDB user document to safe UserResponse (no password)."""
    return UserResponse(
        id=str(user["_id"]),
        full_name=user["full_name"],
        email=user["email"],
        is_active=user.get("is_active", True),
        created_at=user["created_at"].isoformat(),
    )


async def register_user(data: RegisterRequest) -> RegisterResponse:
    """
    Register a new user.

    Steps:
        1. Check if email already exists
        2. Hash password with bcrypt
        3. Save user document to MongoDB
        4. Return safe user object (no password)

    Raises:
        ValueError: If email is already registered.
        RuntimeError: If database is unavailable.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    users = db["users"]

    # 1. Check duplicate email (case-insensitive)
    existing = await users.find_one({"email": data.email.lower()})
    if existing:
        raise ValueError("An account with this email already exists.")

    # 2. Build user document
    now = datetime.now(timezone.utc)
    user_doc = {
        "full_name": data.full_name,
        "email": data.email.lower(),
        "password": hash_password(data.password),
        "is_active": True,
        "created_at": now,
        "updated_at": now,
    }

    # 3. Insert into MongoDB
    result = await users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id

    return RegisterResponse(
        status="success",
        message="Account created successfully. You can now log in.",
        user=_format_user(user_doc),
    )


async def login_user(data: LoginRequest) -> TokenResponse:
    """
    Authenticate user and return JWT tokens.

    Steps:
        1. Find user by email
        2. Verify password using bcrypt
        3. Create access token (15 min) + refresh token (7 days)
        4. Store refresh token in DB for validation
        5. Return both tokens

    Security:
        - Same error message for wrong email AND wrong password
          (prevents user enumeration attacks)

    Raises:
        ValueError: If credentials are invalid.
        RuntimeError: If database is unavailable.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    users = db["users"]

    # 1. Find user — use same generic error for both wrong email & wrong password
    INVALID_CREDENTIALS = "Invalid email or password."

    user = await users.find_one({"email": data.email.lower()})
    if not user:
        raise ValueError(INVALID_CREDENTIALS)

    # 2. Verify password
    if not verify_password(data.password, user["password"]):
        raise ValueError(INVALID_CREDENTIALS)

    # 3. Check account is active
    if not user.get("is_active", True):
        raise ValueError("Your account has been deactivated. Please contact support.")

    # 4. Generate tokens
    user_id = str(user["_id"])
    access_token = create_access_token(user_id=user_id, email=user["email"])
    refresh_token = create_refresh_token(user_id=user_id, email=user["email"])

    # 5. Store refresh token in DB (for validation & logout tracking)
    now = datetime.now(timezone.utc)
    await db["refresh_tokens"].insert_one({
        "user_id": user_id,
        "token": refresh_token,
        "created_at": now,
    })

    # 6. Update last login timestamp
    await users.update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": now}}
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def refresh_access_token(refresh_token: str) -> TokenResponse:
    """
    Issue a new access token using a valid refresh token.
    The old refresh token is invalidated and a new one is issued (token rotation).

    Steps:
        1. Decode & validate refresh token
        2. Check it exists in DB (not already used or revoked)
        3. Delete old refresh token
        4. Issue new access + refresh token pair

    Raises:
        ValueError: If the refresh token is invalid, expired, or already used.
        RuntimeError: If database is unavailable.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    # 1. Decode refresh token
    try:
        payload = decode_refresh_token(refresh_token)
    except ValueError as e:
        raise ValueError(str(e))

    # 2. Check token exists in DB
    stored = await db["refresh_tokens"].find_one({"token": refresh_token})
    if not stored:
        raise ValueError("Refresh token is invalid or has already been used.")

    user_id = payload["sub"]
    email = payload["email"]

    # 3. Rotate — delete old, issue new
    await db["refresh_tokens"].delete_one({"token": refresh_token})

    new_access_token = create_access_token(user_id=user_id, email=email)
    new_refresh_token = create_refresh_token(user_id=user_id, email=email)

    await db["refresh_tokens"].insert_one({
        "user_id": user_id,
        "token": new_refresh_token,
        "created_at": datetime.now(timezone.utc),
    })

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


async def logout_user(access_token: str, refresh_token: str | None = None) -> MessageResponse:
    """
    Logout user by blacklisting their access token.
    Also removes refresh token from DB if provided.

    Why blacklist access tokens?
        JWTs are stateless — we can't "delete" them.
        Blacklisting ensures the token is rejected even before it expires.

    Raises:
        RuntimeError: If database is unavailable.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    now = datetime.now(timezone.utc)

    # 1. Blacklist access token
    await db["token_blacklist"].insert_one({
        "token": access_token,
        "blacklisted_at": now,
    })

    # 2. Remove refresh token from DB if provided
    if refresh_token:
        await db["refresh_tokens"].delete_one({"token": refresh_token})

    return MessageResponse(
        status="success",
        message="Logged out successfully.",
    )


async def get_user_profile(user_id: str) -> UserResponse:
    """
    Fetch user profile by ID.
    Used in the /me endpoint after token validation.

    Raises:
        ValueError: If user not found.
        RuntimeError: If database is unavailable.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("User not found.")

    return _format_user(user)