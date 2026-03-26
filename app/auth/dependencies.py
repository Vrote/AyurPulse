from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bson import ObjectId

from app.auth.jwt_handler import decode_access_token
from app.db.mongodb import get_db

# This tells FastAPI to expect: Authorization: Bearer <token>
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """
    FastAPI dependency — extracts and validates the JWT from the Authorization header.
    Inject this into any route that requires authentication.

    Returns:
        Dict with user_id, email, and role from the database.
    """
    # 1. Check Authorization header exists
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # 2. Decode and validate JWT
    try:
        payload = decode_access_token(token)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check if token is blacklisted (user logged out)
    db = get_db()
    if db is None:
        raise HTTPException(status_code=500, detail="Database connection error.")

    blacklisted = await db["token_blacklist"].find_one({"token": token})
    if blacklisted:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Fetch the full user/doctor from DB for role-based access
    user_doc = await db["users"].find_one({"_id": ObjectId(payload["sub"])})
    if not user_doc:
        user_doc = await db["doctors"].find_one({"_id": ObjectId(payload["sub"])})

    if not user_doc:
         raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account no longer exists.",
             headers={"WWW-Authenticate": "Bearer"},
        )

    return {
        "user_id": str(user_doc["_id"]),
        "email":   user_doc["email"],
        "role":    user_doc.get("role", "user"),
        "full_name": user_doc.get("full_name", "User"),
        "specialization": user_doc.get("specialization") # Important for doctor-based filtering
    }