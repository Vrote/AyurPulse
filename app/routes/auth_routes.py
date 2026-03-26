from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.controllers.auth_controller import (
    register_user,
    register_doctor,
    login_user,
    refresh_access_token,
    logout_user,
    get_user_profile,
)
from app.schemas.auth_schema import (
    RegisterRequest,
    DoctorRegisterRequest,
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    RegisterResponse,
    MessageResponse,
    UserResponse,
    DoctorResponse,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

bearer_scheme = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new account. Password must be 8+ chars with uppercase, digit, and special character.",
)
async def register(data: RegisterRequest):
    try:
        return await register_user(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.post(
    "/doctor/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new doctor",
    description="Create a new professional account for a doctor. Includes medical license details.",
)
async def register_doc(data: DoctorRegisterRequest):
    try:
        return await register_doctor(data)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Doctor registration failed. Please try again."
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password. Returns access token (15 min) and refresh token (7 days).",
)
async def login(data: LoginRequest):
    try:
        return await login_user(data)
    except ValueError as e:
        # 401 for wrong credentials — never 404 (prevents user enumeration)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again."
        )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Exchange a valid refresh token for a new access token + refresh token pair (token rotation).",
)
async def refresh(data: RefreshTokenRequest):
    try:
        return await refresh_access_token(data.refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please log in again."
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout",
    description="Invalidate the current access token. Optionally pass refresh_token in body to revoke it too.",
)
async def logout(
    data: RefreshTokenRequest | None = None,
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    current_user: dict = Depends(get_current_user),
):
    try:
        access_token = credentials.credentials
        refresh_token = data.refresh_token if data else None
        return await logout_user(access_token, refresh_token)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again."
        )


@router.get(
    "/me",
    response_model=UserResponse | DoctorResponse,
    summary="Get current user profile",
    description="Returns the authenticated user's profile. Requires valid Bearer token.",
)
async def get_me(current_user: dict = Depends(get_current_user)):
    try:
        return await get_user_profile(current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not fetch profile. Please try again."
        )