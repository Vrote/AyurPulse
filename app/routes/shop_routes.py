from fastapi import APIRouter, HTTPException, Depends, status

from app.controllers.shop_controller import find_nearby_shops
from app.schemas.shop_schema import NearbyShopsRequest, NearbyShopsResponse
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1/shops",
    tags=["Nearby Shops"]
)


@router.post(
    "/nearby",
    response_model=NearbyShopsResponse,
    summary="Find nearest Ayurvedic shops",
    description=(
        "Send your GPS coordinates to find the 3 nearest Ayurvedic shops. "
        "Uses OpenStreetMap — free, no API key needed. "
        "Frontend gets coordinates from browser: navigator.geolocation.getCurrentPosition(). "
        "Requires login."
    ),
)
async def nearby_shops(
    request: NearbyShopsRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await find_nearby_shops(request)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Shop search failed: {str(e)}"
        )