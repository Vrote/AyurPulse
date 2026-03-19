"""
shop_controller.py
==================
Finds nearest Ayurvedic shops using OpenStreetMap Overpass API.
Uses urllib with increased read timeout — confirmed working on Windows.
"""

import math
import urllib.request
import urllib.parse
import json as json_lib
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.schemas.shop_schema import (
    NearbyShopsRequest,
    NearbyShopsResponse,
    Shop,
)

OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

READ_TIMEOUT = 55  # seconds — Overpass takes ~28s for Pune area queries


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


# ── Query — as simple as possible ─────────────────────────────────────────────
def _build_query(lat: float, lon: float, radius_m: int) -> str:
    """
    Minimal query — only one search tag to minimize server processing time.
    Searches by name containing 'ayurved' (case insensitive).
    """
    return (
        f"[out:json][timeout:30];"
        f"node[\"name\"~\"ayurved\",i]"
        f"(around:{radius_m},{lat},{lon});"
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
        "Shop search is taking too long. "
        "This can take up to 30 seconds — please try again."
    )


# ── Helpers ────────────────────────────────────────────────────────────────────
def _get_name(tags: dict) -> str:
    return (
        tags.get("name") or
        tags.get("name:en") or
        "Ayurvedic Shop"
    )

def _get_address(tags: dict) -> str:
    parts = [
        tags.get("addr:housenumber", ""),
        tags.get("addr:street", ""),
        tags.get("addr:suburb", ""),
        tags.get("addr:city", ""),
    ]
    address = ", ".join(p for p in parts if p)
    return address or "Address not listed"


# ── Main ───────────────────────────────────────────────────────────────────────
async def find_nearby_shops(request: NearbyShopsRequest) -> NearbyShopsResponse:
    radius_m = request.radius_km * 1000
    query    = _build_query(request.latitude, request.longitude, radius_m)

    # Run blocking urllib call in thread pool
    loop = asyncio.get_event_loop()
    try:
        with ThreadPoolExecutor(max_workers=1) as pool:
            data = await loop.run_in_executor(pool, _call_overpass, query)
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Shop search failed: {e}")

    # Parse and sort
    results = []
    for el in data.get("elements", []):
        lat = el.get("lat")
        lon = el.get("lon")
        if lat is None or lon is None:
            continue

        dist = _haversine_km(request.latitude, request.longitude, lat, lon)
        if dist > request.radius_km:
            continue

        tags = el.get("tags", {})
        results.append({
            "name":      _get_name(tags),
            "address":   _get_address(tags),
            "distance":  dist,
            "latitude":  lat,
            "longitude": lon,
            "maps_link": f"https://www.google.com/maps?q={lat},{lon}",
        })

    results.sort(key=lambda x: x["distance"])
    top3 = results[:3]

    shops = [
        Shop(
            name      = s["name"],
            address   = s["address"],
            distance  = f"{s['distance']:.1f} km away",
            latitude  = s["latitude"],
            longitude = s["longitude"],
            maps_link = s["maps_link"],
        )
        for s in top3
    ]

    if shops:
        message = f"Found {len(shops)} Ayurvedic shop(s) near you."
    else:
        message = (
            f"No Ayurvedic shops found within {request.radius_km}km. "
            "Try increasing radius_km to 15 or 20."
        )

    return NearbyShopsResponse(
        status        = "success",
        total         = len(shops),
        shops         = shops,
        message       = message,
        searched_area = f"within {request.radius_km}km of your location",
    )