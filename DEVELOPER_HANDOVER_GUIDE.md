# 🌿 AyurPulse Handover Guide: Full-Stack Architecture & Deep Dive

This document is compiled as a master source of truth for **AyurPulse**, a modern AI-powered Ayurvedic wellness platform. It is structured specifically for an AI coding agent or developer to understand the codebase structure, design patterns, runtime pipelines, database layout, and cross-system integrations in deep technical detail.

---

## 🏛️ 1. System Architecture Overview

AyurPulse is a decoupled full-stack application:
1.  **Frontend**: A responsive React SPA built with **Vite** and styled using **Tailwind CSS**.
2.  **Backend**: An asynchronous REST API built with **FastAPI (ASGI)**.
3.  **Database**: A document-oriented **MongoDB** database accessed asynchronously via the **Motor** driver.
4.  **AI Engine**: A PyTorch **EfficientNet-B2** computer vision pipeline running as a singleton.

```mermaid
graph TD
    subgraph Client [React + Vite Frontend (Port 5173)]
        A[AuthContext / Protected Routes] -->|Axios Interceptors| B(Axios API Client)
        C[Patient Dashboard Wizard] -->|Form Data Image| B
        C -->|JSON Quiz Responses| B
        D[Doctor Vetting Workspace] -->|JSON Plan Updates| B
    end

    subgraph Server [FastAPI Backend (Port 8000)]
        B -->|HTTP Requests| E[main.py ASGI]
        E --> F[Auth Route]
        E --> G[Predictions Route]
        E --> H[Plans Route]
        E --> I[Shops Geolocation Route]

        subgraph ML Pipeline
            G --> J[prediction_model.py Singleton]
            J --> K[EfficientNet-B2 Model]
        end

        subgraph Rules & Geolocation
            H --> L[Prakriti quiz score calculator]
            H --> M[skin_rules.json / ingredient swaps]
            I --> N[Parallel Overpass OSM Racer]
        end
    end

    subgraph Database [MongoDB (Port 27017)]
        F -->|Async Motor| O[(users / doctors / blacklist)]
        G -->|Async Motor| P[(skin_predictions)]
        H -->|Async Motor| Q[(user_plans)]
    end
```

---

## 📁 2. Codebase Directory Map

### 2.1. Root Workspace Layout
*   [app/](file:///c:/Users/Dell/Desktop/Ayurpulse/app) — FastAPI Backend application core code.
*   [frontend/](file:///c:/Users/Dell/Desktop/Ayurpulse/frontend) — Vite React Frontend workspace.
*   [requirements.txt](file:///c:/Users/Dell/Desktop/Ayurpulse/requirements.txt) — Python package dependencies.
*   [run.py](file:///c:/Users/Dell/Desktop/Ayurpulse/run.py) — Entry point script to spawn the Uvicorn web server.
*   [diagnose_db.py](file:///c:/Users/Dell/Desktop/Ayurpulse/diagnose_db.py) — Utility script to test database states and collections.
*   [saved_models/](file:///c:/Users/Dell/Desktop/Ayurpulse/saved_models) — Holds trained weights (`face_skin_disease_model.pth`).
*   [mongodb_data/](file:///c:/Users/Dell/Desktop/Ayurpulse/mongodb_data) — Local MongoDB storage engine directory (ignored in Git).

### 2.2. Backend Directory Structure (`app/`)
*   [app/config/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/config) — Environment settings using `pydantic-settings`.
*   [app/db/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/db) — Motor client initialization and database index registration.
*   [app/models/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/models) — Contains PyTorch model configuration and singleton loader.
*   [app/controllers/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/controllers) — Business logic (AI pipelines, rules engine, geolocation, doctor vetting).
*   [app/routes/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/routes) — API route handlers categorized by router (Auth, Predictions, Plans, Shops).
*   [app/schemas/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/schemas) — Pydantic models enforcing payload validation.
*   [app/utils/](file:///c:/Users/Dell/Desktop/Ayurpulse/app/utils) — Helpers (dosha math, image parsing, logging formatters).

### 2.3. Frontend Directory Structure (`frontend/src/`)
*   `src/components/` — Reusable elements (Navbar, UI cards, layouts).
*   `src/context/` — Global contexts like `AuthContext.jsx`.
*   `src/pages/` — Main layouts (`PatientDashboard.jsx`, `DoctorDashboard.jsx`, `Login.jsx`, `Register.jsx`).
*   `src/services/` — Network request modules (Axios client setup inside `api.js` with interceptors).

---

## 🧠 3. Core Backend Workflows & Implementation Details

### 3.1. Asynchronous Event-Driven Design
The backend is built for non-blocking asynchronous operations. Standard database drivers block the current execution thread when querying, which would freeze the event loop. AyurPulse uses `motor` to process MongoDB queries in a non-blocking way using Python's `async/await` syntax.

### 3.2. AI Diagnostics Pipeline
*   **Model**: EfficientNet-B2 classifier fine-tuned for 5 skin conditions: `acne`, `blackheads`, `dark_spots`, `pores`, `wrinkles`.
*   **Singleton Class (`app/models/prediction_model.py`)**: Loads weights from disk into memory exactly **once** on application boot. This saves 2–5 seconds of latency on incoming requests.
*   **Processing (`app/utils/image_preprocess.py`)**:
    1.  Converts arbitrary image formats into RGB representation.
    2.  Resizes to $224 \times 224$ pixels.
    3.  Normalizes using ImageNet constants (`mean=[0.485, 0.456, 0.406]`, `std=[0.229, 0.224, 0.225]`).
    4.  Transforms with `unsqueeze(0)` to feed the model batch dimensions.
*   **Dynamic Softmax Thresholding**:
    To eliminate false positives, predictions are filtered against class-specific thresholds:
    *   `acne`, `blackheads`, `pores`, `dark_spots` $\ge$ **88.0%**
    *   `wrinkles` $\ge$ **96.0%**

### 3.3. Dosha Quiz & Dynamic Plan Assembly
*   **Dosha Calculation**: A 6-question quiz calculates dominant doshas mapping to `Vata`, `Pitta`, or `Kapha`. The dosha with the highest frequency becomes the dominant Prakriti.
*   **Plan Assembly (`app/controllers/plan_controller.py`)**:
    1.  Loads base templates matching `[detected_condition][dominant_dosha]` from `ayurvedic_plans_v2.json`.
    2.  Reads `skin_rules.json` to swap ingredients based on specific parameters. For instance, if a user has oily skin, standard recipes containing heavy oils are dynamically updated (e.g., coconut oil is swapped with aloe vera gel or jojoba oil).
    3.  Splicing logic integrates age-group guidance, current seasons, and health indicators (like high stress levels).
    4.  Plans are stored with `is_doctor_vetted = False` and placed in the queue matching the condition's medical specialty.

### 3.4. Doctor Specialization-Based Routing
Plans are routed to target medical queues depending on the skin condition:
*   `acne`, `blackheads`, `pores` $\rightarrow$ **Ayurvedic Dermatology**
*   `dark_spots` $\rightarrow$ **Skin Rejuvenation**
*   `wrinkles` $\rightarrow$ **Anti-Aging (Rasayana)**

When doctors audit plans (`PATCH /plan/{plan_id}/review`), the backend runs a safety cleaning block that strips system-level fields (like `id`, `user_id`, `is_doctor_vetted`) from the request payload. This prevents client-side payloads from overwriting structural database state.

### 3.5. Shop Geosearch Parallel Racing (`app/controllers/shop_controller.py`)
To prevent timeouts and 503 errors from free public OpenStreetMap (OSM) Overpass servers:
1.  **Parallel Querying**: Queries **4 global Overpass mirrors in parallel** using a thread pool.
2.  **First-Completed Race**: The first mirror to reply successfully wins, and all other pending mirror queries are aborted immediately via `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`.
3.  **Iterative Expansion**: Starts scanning at **5km**. If fewer than 3 shops are found, it expands the search radius sequentially to **10km, 15km, 20km, and 30km**.
4.  **Haversine Distance**: Calculates the distance from the user's coordinates to the shops to sort results.

---

## 🎨 4. Core Frontend Workflows & Implementation Details

### 4.1. Global Session Context (`AuthContext.jsx`)
Coordinates user role states (`"user"` for patients, `"doctor"` for physicians) and guards protected views. On initialization, it extracts `access_token` from storage, verifies it with the backend (`GET /auth/me`), and populates the global session state.

### 4.2. Silent Token Refresh Interceptors (`frontend/src/services/api.js`)
To handle JWT expiry seamlessly:
*   **Request Interceptor**: Extracts the `access_token` from `localStorage` and injects it as a `Bearer` header on every outbound request.
*   **Response Interceptor**: Intercepts `401 Unauthorized` responses. If a 401 occurs, it halts the request chain, requests new tokens using the `refresh_token` from `POST /api/v1/auth/refresh`, updates `localStorage`, and retries the original request. If the refresh token is expired or revoked, it clears storage and routes the user to `/login`.

### 4.3. React State Immutability
Direct mutations of state objects cause component sync failures. In the Doctor Workspace, before any day-by-day modifications are made, the code performs a **deep copy** of the nested plan state to guarantee rendering updates:
```javascript
const handleStartReview = (plan) => {
  setEditingPlan(JSON.parse(JSON.stringify(plan))); // Deep copy
  setDoctorNotes(plan.doctor_notes || '');
};
```

---

## 🗄️ 5. Database Schema & Indexing Optimization

MongoDB stores all dynamic plan data hierarchically. A single user plan embeds sub-documents for the 7-day schedule, daily morning/evening routine steps, and diet structures. This avoids the 4-way SQL table joins that would degrade database speeds.

### 5.1. Database Collections
1.  **`users`**: Auth profiles, lowercase unique email strings, and hashed passwords.
2.  **`doctors`**: Decoupled professional credentials (specialization, verification status).
3.  **`refresh_tokens`**: Stored active tokens for the rotation logic.
4.  **`token_blacklist`**: Expired/logout JWTs.
5.  **`skin_predictions`**: Logs of CV classifications and raw softmax outputs.
6.  **`user_plans`**: Master generated schedules containing nested schedules and doctor review modifications.

### 5.2. Custom Indexes (`app/db/mongodb.py`)
*   **Unique Index**: Configured on `users.email` and `doctors.email`.
*   **Time-To-Live (TTL) Index**: Configured on `token_blacklist.blacklisted_at` with `expireAfterSeconds=86400` (24 hours). A background thread in MongoDB automatically purges old tokens daily, keeping the collection lightweight.
*   **Compound Indexes**: pre-sort query queries:
    *   `user_plans`: Compound index on `[("user_id", ASCENDING), ("created_at", DESCENDING)]`.
    *   `skin_predictions`: Compound index on `[("user_id", ASCENDING), ("created_at", DESCENDING)]`.

---

## 🚀 6. Local Development Setup & Execution

### 6.1. Environment Configuration
Create a `.env` file in the root directory:
```env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=ayurpulse_db
JWT_SECRET_KEY=your_access_token_secret_key
JWT_REFRESH_SECRET_KEY=your_refresh_token_secret_key
```

### 6.2. Run Backend
```bash
# Activate Virtual Environment
venv\Scripts\activate

# Install Dependencies
pip install -r requirements.txt

# Run FastAPI Server
python run.py
```
*   **REST API Documentation (Swagger)**: Available at `http://127.0.0.1:8000/docs` once running.

### 6.3. Run Frontend
```bash
cd frontend

# Install Dependencies
npm install

# Run Vite dev server
npm run dev
```
*   **App UI Address**: Served at `http://localhost:5173`.

---

## 📝 7. Handover Notes for the Incoming Agent
When modifying this repository, keep these design requirements in mind:
1.  **Always keep database calls non-blocking**: Use `await db[collection].method()` instead of synchronous commands.
2.  **Strip structural metadata on patch requests**: Any update to `user_plans` must clean structural control variables to avoid accidental overwrites of `is_doctor_vetted` flags.
3.  **Ensure React deep-copy integrity**: When editing complex schedules, always deep copy state objects to preserve React's reconciliation engine.
4.  **Preserve the singleton model loading state**: Do not re-initialize the PyTorch loader class inside route handlers; import and access the singleton instead.
