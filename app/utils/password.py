from passlib.context import CryptContext
from fastapi import HTTPException

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    try:
        if len(password.encode("utf-8")) > 72:
            raise HTTPException(
                status_code=400,
                detail="Password too long. Maximum allowed length is 72 characters."
            )

        return pwd_context.hash(password)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Password hashing failed: {str(e)}"
        )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)

    except Exception:
        return False