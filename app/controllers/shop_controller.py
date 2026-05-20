"""
shop_controller.py
==================
Finds nearest Ayurvedic shops using OpenStreetMap Overpass API.
Uses iterative radius expansion to find at least 3 shops.
"""

import math
import urllib.request
import urllib.parse
import json as json_lib
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from app.schemas.shop_schema import (
    NearbyShopsRequest,
    NearbyShopsResponse,
    Shop,
)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

READ_TIMEOUT = 50  # seconds


# ── Distance ───────────────────────────────────────────────────────────────────
def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    R    = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a    = (math.sin(dlat / 2) ** 2 +
            math.cos(math.radians(lat1)) *
            math.cos(math.radians(lat2)) *
            math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# ── Query ──────────────────────────────────────────────────────────────────────
def _build_query(lat: float, lon: float, radius_m: int) -> str:
    """
    Focused node search. 
    Searches by name regex AND healthcare=ayurvedic tag for coverage.
    """
    return (
        f"[out:json][timeout:25];"
        f"("
        f"node[\"name\"~\"ayurved\",i](around:{radius_m},{lat},{lon});"
        f"node[\"healthcare\"=\"ayurvedic\"](around:{radius_m},{lat},{lon});"
        f");"
        f"out 10;"
    )


# ── Sync call ──────────────────────────────────────────────────────────────────
def _call_overpass(query: str) -> dict:
    """Sync urllib POST — runs in thread pool."""
    encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")

    for url in OVERPASS_SERVERS:
        try:
            req = urllib.request.Request(
                url,
                data    = encoded,
                method  = "POST",
                headers = {"Content-Type": "application/x-www-form-urlencoded"},
            )
            with urllib.request.urlopen(req, timeout=READ_TIMEOUT) as r:
                return json_lib.loads(r.read())
        except Exception:
            continue

    raise RuntimeError(
        "Shop search is taking too long or servers are busy. "
        "Please try again in a moment."
    )


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_name(tags: dict) -> str:
    return (
        tags.get("name") or
        tags.get("name:en") or
        "Ayurvedic Shop"
    )

def _get_address(tags: dict) -> str:
    """Robust address extraction from various OSM tags."""
    if tags.get("addr:full"):
        return tags.get("addr:full")

    # Build from components
    parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:housename", ""),
        tags.get("addr:street", ""),
        tags.get("addr:suburb", ""),
        tags.get("addr:district", ""),
        tags.get("addr:city", ""),
    ]
    address = ", ".join(p for p in parts if p)
    
    if not address:
        # Fallback to place/neighbourhood
        alt_parts = [
            tags.get("addr:place", ""),
            tags.get("addr:neighbourhood", ""),
        ]
        address = ", ".join(p for p in alt_parts if p)

    return address or "Address not listed"

def _get_contact(tags: dict, key: str) -> Optional[str]:
    """Extracts contact info like phone or website."""
    val = tags.get(key) or tags.get(f"contact:{key}")
    if key == "phone" and not val:
        val = tags.get("contact:mobile")
    return val


# ── Main ───────────────────────────────────────────────────────────────────────
async def find_nearby_shops(request: NearbyShopsRequest) -> NearbyShopsResponse:
    target_count = 3
    radii_to_try = [5, 10, 15] # km expansion
    final_radius = 5
    all_results = {} # {osm_id: shop_dict} to prevent duplicates

    loop = asyncio.get_event_loop()

    for radius in radii_to_try:
        final_radius = radius
        radius_m = radius * 1000
        query = _build_query(request.latitude, request.longitude, radius_m)

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                data = await loop.run_in_executor(pool, _call_overpass, query)
            
            elements = data.get("elements", [])
            for el in elements:
                osm_id = el.get("id")
                lat, lon = el.get("lat"), el.get("lon")
                if not lat or not lon or osm_id in all_results:
                    continue
                
                dist = _haversine_km(request.latitude, request.longitude, lat, lon)
                tags = el.get("tags", {})
                
                all_results[osm_id] = {
                    "name":      _get_name(tags),
                    "address":   _get_address(tags),
                    "distance":  dist,
                    "latitude":  lat,
                    "longitude": lon,
                    "maps_link": f"https://www.google.com/maps?q={lat},{lon}",
                    "phone":     _get_contact(tags, "phone"),
                    "website":   _get_contact(tags, "website"),
                }
            
            # If we found enough unique shops, stop expanding
            if len(all_results) >= target_count:
                break
        except Exception:
            # If one step fails, try to continue to the next radius unless it was the last one
            if radius == radii_to_try[-1] and not all_results:
                raise
            continue

    # Sort results by distance and pick top 3
    sorted_shops = sorted(all_results.values(), key=lambda x: x["distance"])
    top3 = sorted_shops[:target_count]

    shops = [
        Shop(
            name      = s["name"],
            address   = s["address"],
            distance  = f"{s['distance']:.1f} km away",
            latitude  = s["latitude"],
            longitude = s["longitude"],
            maps_link = s["maps_link"],
            phone     = s["phone"],
            website   = s["website"],
        )
        for s in top3
    ]

    if shops:
        message = f"Found {len(shops)} Ayurvedic shop(s) near you."
        if final_radius > 5:
            message += f" (Expanded search to {final_radius}km to meet requirements)"
    else:
        message = f"No Ayurvedic shops found even within {final_radius}km."

    return NearbyShopsResponse(
        status        = "success",
        total         = len(shops),
        shops         = shops,
        message       = message,
        searched_area = f"within {final_radius}km of your location",
    )