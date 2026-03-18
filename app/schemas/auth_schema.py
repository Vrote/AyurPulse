from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re


class RegisterRequest(BaseModel):
    """Request body for POST /api/v1/auth/register"""
    full_name: str = Field(..., min_length=2, max_length=100, example="Vaishnavi Rote")
    email: EmailStr = Field(..., example="vaishnavi@example.com")
    password: str = Field(..., min_length=8, max_length=64, example="StrongPass@123")

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        """
        Enforce strong password:
        - At least one uppercase letter
        - At least one digit
        - At least one special character
        """
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character.")
        return v

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        return v.strip()


class LoginRequest(BaseModel):
    """Request body for POST /api/v1/auth/login"""
    email: EmailStr = Field(..., example="vaishnavi@example.com")
    password: str = Field(..., example="StrongPass@123")


class TokenResponse(BaseModel):
    """Returned on successful login"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int          # access token lifetime in seconds


class RefreshTokenRequest(BaseModel):
    """Request body for POST /api/v1/auth/refresh"""
    refresh_token: str


class UserResponse(BaseModel):
    """Safe user object — never includes password"""
    id: str
    full_name: str
    email: str
    is_active: bool
    created_at: str


class RegisterResponse(BaseModel):
    status: str = "success"
    message: str
    user: UserResponse


class MessageResponse(BaseModel):
    status: str
    message: str