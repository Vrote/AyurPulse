from fastapi import HTTPException
from app.services.auth_service import *
from app.utils.password import hash_password, verify_password
from app.utils.jwt_handler import create_access_token, create_refresh_token


def register_user(user):

    try:

        if user.password != user.confirm_password:
            raise HTTPException(400, "Passwords do not match")

        existing_user = get_user_by_email(user.email)

        if existing_user:
            raise HTTPException(400, "Email already registered")

        hashed = hash_password(user.password)

        new_user = {
            "name": user.name,
            "email": user.email,
            "password": hashed,
            "login_attempts": 0
        }

        result = create_user(new_user)

        return {
            "message": "User registered successfully",
            "user_id": str(result.inserted_id)
        }

    except Exception as e:
        raise HTTPException(500, str(e))


def login_user(user):

    try:

        db_user = get_user_by_email(user.email)

        if not db_user:
            raise HTTPException(401, "Invalid email or password")

        if not verify_password(user.password, db_user["password"]):
            raise HTTPException(401, "Invalid email or password")

        user_id = str(db_user["_id"])

        access_token = create_access_token({"user_id": user_id})

        refresh_token = create_refresh_token({"user_id": user_id})

        store_refresh_token(user_id, refresh_token)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token
        }

    except Exception as e:
        raise HTTPException(500, str(e))


def logout_user(refresh_token):

    try:

        delete_token(refresh_token)

        return {"message": "Logout successful"}

    except Exception as e:
        raise HTTPException(500, str(e))