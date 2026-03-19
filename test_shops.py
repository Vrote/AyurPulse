"""
Run this to verify the shop query works:
    python test_shops.py
"""
import urllib.request
import urllib.parse
import json
import time

print("Testing minimal Overpass query...\n")

# Minimal single-tag query
query = (
    '[out:json][timeout:30];'
    'node["name"~"ayurved",i]'
    '(around:15000,18.5204,73.8567);'
    'out 10;'
)

data = urllib.parse.urlencode({"data": query}).encode("utf-8")

servers = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

for url in servers:
    print(f"Trying: {url}")
    try:
        start = time.time()
        req = urllib.request.Request(
            url, data=data, method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            body   = r.read()
            elapsed= round(time.time() - start, 1)
            result = json.loads(body)
            count  = len(result.get("elements", []))
            print(f"  PASS in {elapsed}s — found {count} shops")
            for el in result.get("elements", [])[:3]:
                name = el.get("tags", {}).get("name", "Unknown")
                print(f"    → {name}")
            break
    except Exception as e:
        elapsed = round(time.time() - start, 1)
        print(f"  FAIL after {elapsed}s — {e}")