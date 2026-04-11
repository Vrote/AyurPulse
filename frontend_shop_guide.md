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
5.  **Status**: Display the `data.message` so the user knows if the search area was expanded to find them clinics.

> [!TIP]
> Always handle the case where the user denies location permission by showing a fallback (like a search bar for city name).
