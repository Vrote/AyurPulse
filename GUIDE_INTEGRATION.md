# 🔌 AyurPulse Full-Stack Integration Guide: E2E Workflows

This document serves as the comprehensive source of truth for the **full-stack integration** of the **AyurPulse** application. It details how the React frontend merges with the FastAPI backend, describes the network communications, details cross-origin resource sharing (CORS), and provides an end-to-end integration walkthrough.

---

## 🏛️ 1. Full-Stack Data & Network Integration Architecture

```
  ┌────────────────────────┐                   ┌────────────────────────┐
  │   React Frontend       │                   │    FastAPI Backend     │
  │   (Port 5173 / Nginx)  │                   │    (Port 8000 / ASGI)  │
  ├────────────────────────┤                   ├────────────────────────┤
  │ AuthContext & Page     │  HTTP REST (JSON) │ routes/auth_routes.py  │
  │ Axios Client ──────────┼──────────────────>│ routes/plan_routes.py  │
  │                        │<──────────────────┤ routes/shop_routes.py  │
  │ Uploads Dermal Scan ───┼──────────────────>│ routes/pred_routes.py  │
  └────────────────────────┘  multipart/form   └────────────────────────┘
```

The React frontend and FastAPI backend are entirely decoupled, communicating statelessly over **HTTP REST** using JSON payloads, except for image uploads which use `multipart/form-data`.

---

## 🧬 2. End-to-End Integrated Workflows (Step-by-Step)

### 2.1. Authentication & Onboarding Integration
1.  **Patient/Doctor Registers:** The client submits a JSON payload to `POST /api/v1/auth/register` (or `/auth/doctor/register`). The backend validates inputs with Pydantic, hashes passwords using `bcrypt`, and persists records to MongoDB (`users` or `doctors` collections).
2.  **Login Flow & Token Delivery:** 
    *   The user submits credentials to `POST /api/v1/auth/login`.
    *   On validation, the backend generates an **Access Token** (15-min) and a **Refresh Token** (7-day), persists the refresh token in the database, and returns them in the response body.
    *   The React frontend receives the response, saves the tokens in `localStorage`, and updates the global `user` state.
3.  **Active Session Retrieval (`/auth/me`):** On application reload, the React client automatically fires a request containing the Access Token in the header to `GET /api/v1/auth/me`. The backend validates the token, retrieves the user document from the database (filtering out the password hash), and returns it to populate the client-side state.

---

### 2.2. Patient Holistics & AI Plan Generation Integration
The plan generation flow connects the computer vision diagnostic result with the Prakriti rules engine:

```
[Patient: Uploads Photo] ──(multipart/form)──> POST /api/v1/predictions/predict
                                                         │
                                               [Return prediction_id]
                                                         │
                                                         ▼
[Patient: Submits Quiz] ───(JSON payload)─────> POST /api/v1/plan/generate
                                               (Includes prediction_id + Quiz JSON)
```

1.  **Skin Diagnostic Upload:** 
    *   The patient uploads a face scan in the dashboard. React wraps the image in a `FormData` object and calls `POST /api/v1/predictions/predict`.
    *   The backend validates file constraints (max 5MB), saves it to `uploads/` with a UUID prefix, normalizes the pixels into a PyTorch tensor, runs EfficientNet-B2 inference, filters results using dynamic thresholds, logs the results in `skin_predictions`, and returns a unique **`prediction_id`** alongside detected conditions.
2.  **Dosha Quiz & Parameter Splicing:**
    *   The patient completes the 6-question Prakriti quiz and selects parameters like skin type, age, and season.
    *   React compiles these responses alongside the `prediction_id` into a JSON payload and calls `POST /api/v1/plan/generate`.
    *   The backend retrieves the prediction record using the `prediction_id`, calculates the dominant Dosha from the quiz responses, retrieves the corresponding master plan template, applies ingredients swaps from `skin_rules.json` in memory, saves the plan in `user_plans` in an **unvetted state** (`is_doctor_vetted = False`), and returns the plan JSON to the client.

---

### 2.3. Doctor Vetting Queue & Integration
1.  **Specialization Queue Fetching:** 
    *   When a doctor logs in, the doctor dashboard queries `GET /api/v1/plan/unchecked-plans` (or `/plan/reviewed-plans` for logs).
    *   The backend inspects the doctor's specialization and filters pending plans dynamically: doctors only see plans matching their specialty (e.g. anti-aging specialists only see wrinkle plans).
2.  **Inline Modifications & Verification Submission:**
    *   The doctor reviews the plan on the client-side, making edits to daily themes, routines, diets, or adding custom annotation notes.
    *   The doctor clicks "Approve & Save Vetted Plan," prompting React to call `PATCH /api/v1/plan/{plan_id}/review` carrying the updated plan payload.
    *   The backend strips sensitive fields (like system IDs) to prevent modifications, updates the plan's vetting state flags, and sets `is_doctor_vetted = True`.
3.  **Patient Visual Verification:** When the patient next opens their dashboard, the frontend fetches the plan. Since `is_doctor_vetted` is now `True`, the dashboard displays a premium **Verified Green Badge** alongside the doctor's custom notes and signed name.

---

### 2.4. Shop Locator Integration
*   The patient searches for nearby Ayurvedic shops from their dashboard.
*   React requests the browser's geolocation API or processes coordinate inputs, sending them to `POST /api/v1/shops/nearby`.
*   The backend races Overpass API mirrors to find pharmacy coordinates, performs Haversine calculations to compute distances, expands the search area dynamically if needed, and returns the top 3 closest shops.
*   The frontend receives the list, maps coordinates to an interactive **OpenStreetMap** container, and provides direct Google Maps navigation links.

---

## 🛠️ 3. Cross-Origin Resource Sharing (CORS) Setup

Because the frontend runs on port `5173` (or port `80` in production) and the backend runs on port `8000`, browsers will block API calls due to **Same-Origin Policy** unless CORS is explicitly allowed in the backend.

FastAPI is configured to allow secure communication in `app/main.py` using middleware:

```python
from fastapi.middleware.cors import CORSMiddleware

# List of allowed client origins (development and production hosts)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:80",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,      # Crucial to permit authorization headers and cookies
    allow_methods=["*"],          # Permits all standard REST methods (GET, POST, PATCH, OPTIONS, etc.)
    allow_headers=["*"],          # Permits all client request headers
)
```

---

## 💡 4. Interview Focus: Common Integration Questions

#### Q1: How do your frontend and backend communicate securely?
**A:** They communicate statelessly over HTTPS. Upon successful login, the backend issues a JSON Web Token (JWT) access token. The frontend stores this token in memory or `localStorage`. Using an Axios request interceptor, the client automatically injects this token into the `Authorization` header as a `Bearer` token for all subsequent requests. The backend parses this header, decodes the signature, and verifies the user's identity on every endpoint call.

#### Q2: How does the image upload integration work under the hood?
**A:** Standard JSON payloads cannot transmit raw file binaries efficiently. To handle image uploads, the React frontend wraps the image binary and metadata in a `FormData` object, which sets the HTTP header `'Content-Type': 'multipart/form-data; boundary=...'`. The backend FastAPI endpoint declares the input parameter as a `UploadFile` (using `File` and `Form` dependencies), allowing Python to stream the uploaded image binary directly into memory or disk storage.

#### Q3: Why is CORS necessary, and how is it secured in your application?
**A:** Cross-Origin Resource Sharing (CORS) is a browser security mechanism that prevents malicious websites from reading sensitive data from another domain. In development, our frontend is served from `localhost:5173` while our backend listens on `localhost:8000`. Without explicit CORS middleware, the browser would block the frontend from reading the backend's responses. We secure this by configuring FastAPI's `CORSMiddleware` with a strict, whitelisted list of origins, preventing arbitrary third-party domains from querying our API.
