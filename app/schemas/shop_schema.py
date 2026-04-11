from pydantic import BaseModel, Field
from typing import List, Optional


class NearbyShopsRequest(BaseModel):
    """
    Frontend sends user's GPS coordinates from browser.
    Frontend code: navigator.geolocation.getCurrentPosition(...)
    """
    latitude:  float = Field(..., example=18.5204,
        description="User's latitude from browser GPS")
    longitude: float = Field(..., example=73.8567,
        description="User's longitude from browser GPS")
    radius_km: int   = Field(5, ge=1, le=20,
        description="Search radius in km. Default 5km, max 20km.")


class Shop(BaseModel):
    name:      str
    address:   str
    distance:  str           # e.g. "1.2 km away"
    latitude:  float
    longitude: float
    maps_link: str           # opens Google Maps with pin
    phone:     Optional[str] = None
    website:   Optional[str] = None


class NearbyShopsResponse(BaseModel):
    status:    str = "success"
    total:     int
    shops:     List[Shop]
    message:   str
    searched_area: str      # e.g. "within 5km of your location"