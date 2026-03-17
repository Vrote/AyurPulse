from fastapi import APIRouter
from app.models.user_model import RegisterSchema, LoginSchema
from app.controllers.auth_controller import *

router = APIRouter()


@router.post("/register")
def register(user: RegisterSchema):
    return register_user(user)


@router.post("/login")
def login(user: LoginSchema):
    return login_user(user)


@router.post("/logout")
def logout(refresh_token: str):
    return logout_user(refresh_token)