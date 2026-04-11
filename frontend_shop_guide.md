# AyurPulse: Frontend Integration Guide (Nearby Shops)

To integrate the new **Auto-Expanding Shop Search** into your React frontend, follow this guide.

## 1. The API Endpoint
- **URL**: `POST http://127.0.0.1:8000/api/v1/shops/nearby`
- **Auth**: Requires `Bearer <access_token>` in the headers.

### Request Body (JSON)
```json
{
  "latitude": 18.5204, 
  "longitude": 73.8567,
  "radius_km": 5
}
```

### Response Example
```json
{
  "status": "success",
  "total": 3,
  "shops": [
    {
      "name": "Vishvand Ayurvedic Clinic",
      "address": "Pune, Maharashtra",
      "distance": "4.7 km away",
      "latitude": 18.4904025,
      "longitude": 73.8248393,
      "maps_link": "https://www.google.com/maps?q=18.4904,73.8248",
      "phone": "094225 66929",
      "website": null
    }
  ],
  "message": "Found 3 Ayurvedic shop(s) near you. (Expanded search to 10km to meet requirements)",
  "searched_area": "within 10km of your location"
}
```

---

## 2. React Implementation Example

### a) Getting the user's location
Use the browser's built-in `navigator.geolocation` API:

```javascript
const getShops = () => {
  navigator.geolocation.getCurrentPosition(async (position) => {
    const { latitude, longitude } = position.coords;
    
    // Call your API
    const response = await fetch("http://127.0.0.1:8000/api/v1/shops/nearby", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
      },
      body: JSON.stringify({ latitude, longitude, radius_km: 5 })
    });
    
    const data = await response.json();
    setShops(data.shops);
  });
};
```

---

## 3. "Real World" User Flow

1.  **Trigger**: User clicks a **"Find Nearest Ayurvedic Clinics"** button on their dashboard.
2.  **Permission**: The browser UI pops up: *"AyurPulse wants to access your location"*. User clicks **Allow**.
3.  **Loading**: Show a spinner. Behind the scenes, the backend is searching 5km, 10km, etc., until it finds 3 clinics.
4.  **Display**:
    - Show a list of the 3 clinics.
    - Each clinic should have a **"View on Maps"** button (using `maps_link`).
    - If `phone` is available, show a **"Call Now"** link: `<a href={`tel:${shop.phone}`}>Call</a>`.
5.  **Status**: Display the `data.message` so the user knows if the search area was expanded.

## 4. Handling Empty Fields (Null Checks)
OpenStreetMap data is sometimes incomplete. The API returns `null` if a field like `phone` or `website` is missing. Your React code **must** check for this before rendering:

```javascript
{shops.map((shop) => (
  <div key={shop.latitude}>
    <h3>{shop.name}</h3>
    <p>Distance: {shop.distance}</p>
    
    {/* Only show Phone if it exists */}
    {shop.phone ? (
      <a href={`tel:${shop.phone}`} className="btn">Call {shop.phone}</a>
    ) : (
      <span className="info">No phone number provided</span>
    )}

    {/* Only show Website button if URL exists */}
    {shop.website && (
      <a href={shop.website} target="_blank">Visit Website</a>
    )}
    
    {/* Always show Address fallback if missing */}
    <p>Address: {shop.address || "Search nearby area for details"}</p>
  </div>
))}
```

> [!TIP]
> Use Optional Chaining (`shop?.phone`) and standard JavaScript falsy checks (`if (shop.phone)`) to keep the UI clean and prevent crashes.
