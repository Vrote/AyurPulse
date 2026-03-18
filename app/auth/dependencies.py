from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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

    Usage in route:
        @router.get("/profile")
        async def profile(current_user: dict = Depends(get_current_user)):
            ...

    Returns:
        Dict with user_id and email from the token payload.

    Raises:
        401 Unauthorized if token is missing, expired, or invalid.
        401 Unauthorized if the token has been blacklisted (logged out).
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
    if db is not None:
        blacklisted = await db["token_blacklist"].find_one({"token": token})
        if blacklisted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been invalidated. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return {
        "user_id": payload["sub"],
        "email": payload["email"],
    }