import httpx
import json

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_shops():
    print("Testing Ayurvedic Pharmacy Finder (Backend Expansion)...")
    
    # 1. Login to get token (using an existing user or registering one)
    client = httpx.Client(timeout=30.0)
    email = "shoptest@example.com"
    password = "Password@123"
    
    # Try login first
    login_resp = client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if login_resp.status_code != 200:
        # Register
        client.post(f"{BASE_URL}/auth/register", json={"full_name": "Shop Tester", "email": email, "password": password})
        login_resp = client.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    
    token = login_resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    
    # Test Near Pune (Coordinates with known results)
    payload = {
        "latitude": 18.5204,
        "longitude": 73.8567,
        "radius_km": 5
    }
    
    print(f"Requesting shops near {payload['latitude']}, {payload['longitude']}...")
    resp = client.post(f"{BASE_URL}/shops/nearby", json=payload)
    print(f"Status: {resp.status_code}")
    
    if resp.status_code == 200:
        data = resp.json()
        print(f"Message: {data['message']}")
        print(f"Total found: {data['total']}")
        for s in data['shops']:
            print(f"- {s['name']} ({s['distance']})")
    else:
        print(f"Error: {resp.text}")

if __name__ == "__main__":
    test_shops()
