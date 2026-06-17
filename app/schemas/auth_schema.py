from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, Union
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


class DoctorRegisterRequest(RegisterRequest):
    """Specific request for Doctor registration with professional details."""
    specialization: str = Field(..., description="e.g. Ayurvedic Dermatology, General Ayurveda")
    clinic_address: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)


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
    role: str
    created_at: str


class DoctorResponse(BaseModel):
    """Detailed doctor profile for frontend/admin review."""
    id: str
    full_name: str
    email: str
    specialization: str
    clinic_address: Optional[str]
    is_active: bool = True
    
    is_verified: bool
    role: str = "doctor"
    created_at: str


class RegisterResponse(BaseModel):
    status: str = "success"
    message: str
    user: Union[UserResponse, DoctorResponse]


class MessageResponse(BaseModel):
    status: str
    message: str