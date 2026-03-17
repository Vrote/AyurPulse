from fastapi import Request, HTTPException
from app.utils.jwt_handler import verify_token
from app.config.settings import settings


async def auth_middleware(request: Request):

    token = request.headers.get("Authorization")

    if not token:
        raise HTTPException(401, "Token missing")

    token = token.split(" ")[1]

    payload = verify_token(
        token,
        settings.ACCESS_TOKEN_SECRET
    )

    if not payload:
        raise HTTPException(401, "Invalid token")

    return payload