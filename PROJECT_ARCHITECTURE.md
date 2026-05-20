# AyurPulse Project Architecture & Technical Guide

This document serves as the comprehensive source of truth for the **AyurPulse** application. Any future developer or AI agent should read this file to understand the system architecture, database models, AI pipelines, API routing, and code structure.

---

## 📂 Codebase Layout

```text
Ayurpulse/ (Repository Root)
├── Ayurpulse/                   # FastAPI Backend
│   ├── app/
│   │   ├── config/              # Environment configurations & settings
│   │   ├── controllers/         # Core business logic (Inference, Plan generation, Vetting)
│   │   ├── db/                  # MongoDB async connection & collections setup
│   │   ├── models/              # Model structure definitions & loaders
│   │   ├── routes/              # FastAPI Router endpoints (Auth, Plans, Predictions, Shops)
│   │   ├── schemas/             # Pydantic input/output schemas
│   │   └── utils/               # Helper modules (Dosha assessment, Image preprocessing, Logging)
│   ├── logs/                    # Local server logs (ayurpulse.log)
│   ├── saved_models/            # Trained PyTorch Model weights (.pth)
│   ├── uploads/                 # Uploaded patient skin scan images
│   ├── run.py                   # Entrypoint script to start the Uvicorn server
│   └── test_integration.py      # E2E integration test suite
│
├── frontend/                    # Vite + React Frontend
│   ├── src/
│   │   ├── assets/              # Icons, images, and static graphics
│   │   ├── components/          # Reusable UI components
│   │   ├── context/             # Authentication & global React contexts
│   │   ├── pages/               # Main dashboard views (Patient, Doctor, Auth, Landing)
│   │   └── services/            # Axios API client setup and interceptors
│   ├── package.json
│   └── tailwind.config.js       # Styling definitions
│
└── PROJECT_ARCHITECTURE.md      # This file
```

---

## ⚙️ Backend Architecture (FastAPI + MongoDB + PyTorch)

The backend handles user authentication, computer vision skin analysis, personalized health plan assembly, expert auditing, and pharmacy geolocation.

### 1. Database Schema & Collections (MongoDB)
Database connection is asynchronously managed via the **Motor** driver.
*   `users`: Stores both patient profiles and doctor profiles (differentiated by `role` field: `"user"` vs `"doctor"`).
*   `doctors`: Contains extended professional details (specialization, experience, clinic address) linked to user records.
*   `refresh_tokens` & `token_blacklist`: Manages stateless JWT authentication security flow.
*   `skin_predictions`: Logs skin scan uploads, detected classes, and raw probabilities.
*   `user_plans`: Houses generated 7-day schedules, personalized notes, and doctor vetting states.

### 2. AI Diagnostics Engine
*   **Model**: EfficientNet-B2 fine-tuned on skin conditions. Loaded as a singleton in `app/models/prediction_model.py`.
*   **Target Classes**: `acne`, `blackheads`, `dark spots`, `pores`, `wrinkles`.
*   **Thresholding**: Applied dynamically per-class (e.g., higher confidence threshold for wrinkles).
*   **Output**: Saves diagnostic records to `skin_predictions` and outputs a `prediction_id` to link with plan creation.

### 3. Dynamic Plan Assembly (Rule Engine)
*   **Inputs**: A `prediction_id` (representing the primary detected skin issue) and answers to a **6-question Prakriti (Dosha) Quiz**.
*   **Calculation**: Maps quiz answers to Vata, Pitta, or Kapha dominance.
*   **Assembly**:
    1. Loads base plans from `ayurvedic_plans_v2.json` for the condition/dosha pairing.
    2. Modifies instructions using ingredients swaps from `skin_rules.json` depending on the patient's skin type, age, season, and lifestyle factors.
    3. Saves the final plan to the database and marks it as awaiting review.

### 4. Specialization Routing & Vetting
*   Plans require vetting by an Ayurvedic doctor matching the specialization of the detected condition:
    *   `acne` / `blackheads` / `pores` ➜ `Ayurvedic Dermatology`
    *   `dark_spots` ➜ `Skin Rejuvenation`
    *   `wrinkles` ➜ `Anti-Aging (Rasayana)`
*   Doctors query their specialized queue via `GET /plan/unchecked-plans`.
*   **Vetting Bug Alert**:
    *   In `app/controllers/plan_controller.py`, when a doctor sends a modified plan to `PATCH /plan/{plan_id}/review`, the backend merges the `modified_plan` payload: `update_data.update(request.modified_plan)`.
    *   Because `modified_plan` is usually a copied object from the unchecked queue, it carries `"is_doctor_vetted": false`. This overwrites the doctor's vetting confirmation flag back to `false` in the database.
    *   **Fix**: Ensure `"is_doctor_vetted"` (along with other state flags) is removed from `request.modified_plan` before performing the dictionary update.

### 5. Shop Geolocation
*   **Endpoint**: `POST /shops/nearby`
*   **Mechanism**: Queries OpenStreetMap Overpass API for pharmacies/clinics near patient coordinates.
*   **Radius Expansion**: Starts at 5km. Dynamically expands to 10km, then 15km if fewer than 3 shops are found to guarantee results in remote locations.

---

## 🖥️ Frontend Architecture (Vite + React + Tailwind)

A modern single-page dashboard app providing a seamless wizard flow for patient diagnosis and a management portal for doctors.

### 1. Authentication & API Client
*   **`AuthContext.jsx`**: Coordinates role-based routing (Redirects patients to `/dashboard` and doctors to `/doctor-dashboard`).
*   **`api.js`**: Axios helper that automatically injects JWT bearer tokens from `localStorage`. Implements an interceptor that catches `401 Unauthorized` errors, automatically queries `POST /auth/refresh`, replaces tokens, and retries the failed request.

### 2. Dashboard Pages
*   **`PatientDashboard.jsx`**:
    *   *Scan Step*: Patients take/upload a photo.
    *   *Quiz Step*: Multi-choice questionnaire.
    *   *Customization*: Selects lifestyle (e.g. poor sleep, high stress), season, and skin type.
    *   *Results/Plan View*: Visualizes morning routines, afternoon diets, evening treatments, and daily yoga. Displays a verified checkmark if vetted by a doctor, along with doctor notes.
*   **`DoctorDashboard.jsx`**:
    *   Lists specialization-specific unchecked queues and historical reviewed plans.
    *   Provides an inline, day-by-day scheduler editor to modify recommendations, add expert notes, and submit approvals.

---

## 🧪 Testing & Verification

*   Run backend dev server:
    ```powershell
    cd Ayurpulse
    .\venv\Scripts\python run.py
    ```
*   Run frontend dev server:
    ```powershell
    cd frontend
    npm run dev
    ```
*   Run integration tests (requires backend running):
    ```powershell
    cd Ayurpulse
    $env:PYTHONIOENCODING="utf-8"
    .\venv\Scripts\python test_integration.py
    ```
