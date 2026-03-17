from jose import jwt, JWTError
from datetime import datetime, timedelta
from app.config.settings import settings

ALGORITHM = "HS256"


def create_access_token(data: dict):

    expire = datetime.utcnow() + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    data.update({"exp": expire})

    return jwt.encode(
        data,
        settings.ACCESS_TOKEN_SECRET,
        algorithm=ALGORITHM
    )


def create_refresh_token(data: dict):

    expire = datetime.utcnow() + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )

    data.update({"exp": expire})

    return jwt.encode(
        data,
        settings.REFRESH_TOKEN_SECRET,
        algorithm=ALGORITHM
    )


def verify_token(token: str, secret: str):

    try:
        payload = jwt.decode(
            token,
            secret,
            algorithms=[ALGORITHM]
        )

        return payload

    except JWTError:
        return None