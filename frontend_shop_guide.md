# AyurPulse: Frontend Shop Integration Guide (Agent-Ready)

This document provides a comprehensive specification for an AI agent to integrate the **Ayurvedic Shop Search** into a React application.

## 1. Context for the Integrating Agent
The backend implements an **Iterative Auto-Expanding Search**. It uses the OpenStreetMap Overpass API through a Python FastAPI controller.
- **Backend Logic**: Starts at a 5km radius. If < 3 results are found, it expands to 10km, then 15km.
- **Data Quality**: The backend extracts `name`, `address` (parsed from multiple OSM tags), `distance` (haversine), `phone`, and `website`.

---

## 2. API Technical Specification

### Endpoint: `POST /api/v1/shops/nearby`
- **Method**: `POST`
- **Authentication**: Bearer Token required in `Authorization` header.
- **Content-Type**: `application/json`

### Request Payload (JSON)
| Field | Type | Description |
| :--- | :--- | :--- |
| `latitude` | `float` | User's current latitude coordinate. |
| `longitude` | `float` | User's current longitude coordinate. |
| `radius_km` | `int` | Initial search radius (default 5). Backend will expand this if needed. |

### Response Payload (JSON)
| Field | Type | Handling Requirement |
| :--- | :--- | :--- |
| `status` | `string` | "success" or "error". |
| `total` | `int` | Number of shops returned (usually top 3). |
| `shops` | `array` | List of `Shop` objects (see below). |
| `message` | `string` | User-facing message. **Must display** this as it contains radius expansion info. |
| `searched_area`| `string` | Description of the final radius used (e.g., "within 10km"). |

### Shop Object Structure
| Field | Type | Handling / Null Checks |
| :--- | :--- | :--- |
| `name` | `string` | Always present. Fallback to "Ayurvedic Shop". |
| `address` | `string` | Can be "Address not listed". Use `||` fallback in UI. |
| `distance` | `string` | Pre-formatted string (e.g., "4.7 km away"). |
| `maps_link` | `string` | Google Maps URL. Use for "View Map" action. |
| `phone` | `string?` | **COULD BE NULL**. Render call button conditionally. |
| `website` | `string?` | **COULD BE NULL**. Render link conditionally. |

---

## 3. Integration Logic for React
### a) Location Acquisition
Use `navigator.geolocation.getCurrentPosition`. Handle the `PermissionDeniedError` case by allowing manual coordinates entry or showing a friendly warning.

### b) API State Management
Maintain a state for `loading`, `error`, and `shops`. 
- **Wait Time**: Note that the search can take 10-25 seconds due to Overpass API lookups and expansions. Show a non-generic loader (e.g., "Searching for nearest Ayurvedic clinics...").

### c) UI Implementation Example (Snippet)
```javascript
// Example logic for the integrating agent
const handleFindShops = () => {
  setIsLoading(true);
  navigator.geolocation.getCurrentPosition(
    async (pos) => {
      try {
        const response = await api.post("/shops/nearby", {
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
          radius_km: 5
        });
        setShops(response.data.shops);
        setSearchMessage(response.data.message);
      } catch (err) {
        setError("Unable to find shops. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    },
    (err) => {
      setError("Location permission denied.");
      setIsLoading(false);
    }
  );
};
```

---

## 4. Troubleshooting for Agents
- **503 Status**: If the backend returns 503, the Overpass servers are likely busy. Implement a retry button.
- **Empty Phone/Website**: Always use optional chaining or falsy checks to avoid "Cannot read property of null" errors.
- **CORS**: Ensure the React app domain is whitelisted in the FastAPI `CORSMiddleware`.
