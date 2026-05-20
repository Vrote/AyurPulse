# AyurPulse Frontend Integration Guide

Welcome to the AyurPulse frontend development phase! The backend is fully developed and running a FastAPI server (typically at `http://127.0.0.1:8000`). This document outlines everything you need to know about the API endpoints, data models, authentication flow, and User Interface requirements.

## 1. Setup & Configuration
- **Base URL:** `http://127.0.0.1:8000/api/v1`
- **Swagger Documentation:** Available at `http://127.0.0.1:8000/docs`. You can test endpoints directly from here using the `Authorize` button.
- **Authentication:** The app uses JWT (JSON Web Tokens). Protected endpoints require a Bearer token:
  `Authorization: Bearer <access_token>`

---

---

## 2. User Roles
The application supports two primary user roles:
1. **Patient (User):** Can upload images for skin analysis, complete Dosha assessments, generate customized Ayurvedic plans, and search for nearby Ayurvedic shops.
2. **Doctor:** Can register with professional credentials, view unchecked system-generated Ayurvedic plans relevant to their specialization, and review/modify plans for patients.

When calling `GET /auth/me`, the response will have a `role` field (`"user"` or `"doctor"`), which you should use in the frontend to conditionally render the Patient Dashboard vs. the Doctor Dashboard.

---

## 3. Authentication Flow (Applies to both Roles)

### a) Registration
**Endpoint:** `POST /auth/register` (Patient)
**Body:**
```json
{
  "full_name": "John Doe",
  "email": "john@example.com",
  "password": "StrongPassword@123" // Must contain uppercase, digit, and special char
}
```

**Endpoint:** `POST /api/v1/auth/doctor/register` (Doctor)
**Body:**
```json
{
  "full_name": "Dr. Smith",
  "email": "smith@example.com",
  "password": "StrongPassword@123",
  "specialization": "Ayurvedic Dermatology", // UI Note: Implement as a Dropdown
  "clinic_address": "123 Wellness Ave",
  "experience_years": 5
}
```

> **UI Implementation Note for Specialization:**
> To prevent typos and ensure correct routing of patient plans, the `specialization` field **must be a dropdown menu** on the registration page, not a free-text input. 
> 
> **Available Options to display:**
> - `Ayurvedic Dermatology` (For acne, blackheads, pores)
> - `Skin Rejuvenation` (For dark spots)
> - `Anti-Aging (Rasayana)` (For wrinkles)
> - `General Ayurveda` (Can review any plan)

### b) Login
**Endpoint:** `POST /api/v1/auth/login`
**Body:** `{"email": "...", "password": "..."}`
**Response:** Gives you an `access_token` and `refresh_token`. Store the `access_token` in memory or sessionStorage, and the `refresh_token` securely (e.g., HTTPOnly cookie or localStorage if needed for SPA).

### c) Refresh Token
**Endpoint:** `POST /api/v1/auth/refresh`
If the access token expires (usually after 15 mins), send the refresh token to get a new pair.
**Body:** `{"refresh_token": "<token>"}`

### d) Current User Profile
**Endpoint:** `GET /api/v1/auth/me`
**Headers:** `Authorization: Bearer <access_token>`
Call this on app load (if token exists) to hydrate the user context in React (e.g., Redux or Context API).

---

## 4. UI Flow: Patient (User)

### Step 1: Skin Analysis (Image Upload)
**Endpoint:** `POST /api/v1/predict`
- **Request Type:** `multipart/form-data`
- **Field Name:** `file` (Send a JPG/PNG up to 5MB).
- **Response:** Contains `prediction_id`, `detected_conditions`, and a `message`.
- **UI Action:** Show the detected conditions to the user. Save the `prediction_id` in React state because you will need it for the next step.

### Step 2: Dosha Assessment
**Endpoint:** `GET /api/v1/plan/questions` (Public)
- **Response:** Returns the 6 core questions for the Prakriti (Dosha) assessment.
- **UI Action:** Render a wizard/form for the user to select answers.

### Step 3: Plan Generation
**Endpoint:** `POST /api/v1/plan/generate`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body Requirement:**
```json
{
  "prediction_id": "<ID_FROM_STEP_1>",
  "dosha_answers": {
    "body_frame": "small_thin",
    "hunger": "irregular",
    "sleep": "light",
    "feeling": "cold",
    "digestion": "gas_bloat",
    "mood": "quick_anxious"
  },
  "skin_type": "oily",
  "age_group": "21-30",
  "season": "summer",
  "lifestyle": ["high_stress", "poor_sleep"]
}
```

> **UI Implementation Note for Plan Form Fields:**
> The frontend must provide the exact options the backend expects (no free text):
> 
> **1. Dosha Answers Options** (Use Radio Buttons):
> - `body_frame`: `"small_thin"`, `"medium"`, `"large_heavy"`
> - `hunger`: `"irregular"`, `"very_strong"`, `"slow"`
> - `sleep`: `"light"`, `"sound"`, `"deep"`
> - `feeling`: `"cold"`, `"hot"`, `"cool"`
> - `digestion`: `"gas_bloat"`, `"burning"`, `"heavy"`
> - `mood`: `"quick_anxious"`, `"focused_irritable"`, `"calm"`
> 
> **2. Profile Specifics Options** (Use Dropdowns or Radios):
> - `skin_type`: `"oily"`, `"dry"`, `"sensitive"`, `"combination"`, `"normal"`
> - `age_group`: `"10-20"`, `"21-30"`, `"31-40"`, `"40+"`
> - `season`: `"summer"`, `"winter"`, `"monsoon"`, `"autumn"`
> - `lifestyle` (Multi-Select Checkboxes): Allowed values are `"high_stress"`, `"low_water"`, `"vegan"`, `"female"`, `"poor_sleep"`

- **Response:** Returns a full JSON object with a 7-day Ayurvedic plan (`days` array with `morning`, `diet`, `evening`, `yoga`).
- **UI Action:** Display this beautifully. Note the flags `is_doctor_vetted` (boolean). If false, show a UI badge "Pending Doctor Review". If true, show "Verified by Dr. <name>". 

### Step 4: History Views
**Retrieve Prediction (Scan) History**
**Endpoint:** `GET /api/v1/predict/history`
- **Headers:** `Authorization: Bearer <access_token>`
- **UI Action:** Fetch this on the Patient Dashboard to show a grid of past skin scan results, allowing the patient to reference past AI detections.

**Retrieve Plan History**
**Endpoint:** `GET /api/v1/plan/history`
- **Headers:** `Authorization: Bearer <access_token>`
- **UI Action:** Fetch this to show a timeline of the user's generated Ayurvedic plans. If a plan in the history array has `is_doctor_vetted: true`, dynamically render it with a green "Verified" checkmark!

### Step 5: Map/Shops View
**Endpoint:** `POST /api/v1/shops/nearby`
- Use the HTML5 Geolocation API (`navigator.geolocation.getCurrentPosition()`) to get latitude/longitude.
- **Body:** `{"latitude": 18.5204, "longitude": 73.8567, "radius_km": 5}`
- **UI Action:** Render the returned shops. Each shop has a `maps_link` to open Google Maps, and optional `phone` and `website` fields.

---

## 5. UI Flow: Doctor

### Step 1: Doctor Dashboard
Check role from `GET /api/v1/auth/me`. If role `doctor`, route to doctor dashboard.

### Step 2: View Unchecked Plans (Patient List)
**Endpoint:** `GET /api/v1/plan/unchecked-plans`
- **Headers:** `Authorization: Bearer <access_token>`
- **UI Action:** Display a list/table showing the **User/Patient Name** for each unchecked plan. This list is automatically filtered by the backend so the doctor only sees patients relevant to their `specialization`.

### Step 3: Detailed Editable Plan View
**UI Action:** When a doctor clicks on a **User's Name** (from either the **Unchecked** or **Checked** patient lists), the frontend must route to a **new dedicated web page** (or full-screen view) displaying that specific patient's **entire plan**.
- **Important:** The plan must not be read-only! Every single field of the patient's generated plan (routines, ingredients, diet, etc.) must be rendered inside **editable form inputs / textareas**.
- The doctor can read and directly modify the patient's plan in these same fields.
- There must be a specific text area to add `doctor_notes`.
- At the bottom, provide a **"Save Plan"** button.

### Step 4: Saving the Reviewed / Edited Plan
**Endpoint:** `PATCH /api/v1/plan/{plan_id}/review`
- **Headers:** `Authorization: Bearer <access_token>`
- **Body Requirement:**
```json
{
  "is_doctor_vetted": true,
  "doctor_notes": "Added more hydration tips.",
  "modified_plan": { ... } // Pass the entire modified JSON object from the editable form fields
}
```
- **Note:** This works for both Unchecked and Checked plans. A doctor can always open a previously checked plan, edit the fields again, and hit save to update it!

### Step 5: View Checked Plans
**Endpoint:** `GET /api/v1/plan/reviewed-plans`
- Shows previously checked plans by this doctor. As mentioned above, clicking on any of these must open the same Editable Plan View (Step 3).

---

## Summary of Key Frontend Tasks for React Developer:
1. **Setup React Router** with Private Routes (checking for auth token).
2. **Setup Axios/Fetch interceptor** to automatically attach `Bearer` token and handle 401 Unauthorized by calling `/refresh`.
3. **Build Authentication Forms:** Login, Patient Register, Doctor Register.
4. **Build Image Upload Component:** Ensure it handles `multipart/form-data` correctly.
5. **Build Plan Generator Wizard:** A multi-step flow: Upload Image -> Get Questions -> Answer Dosha form -> Submit Generation -> View Result.
6. **Build Dashboards:**
   - **Patient:** Show latest scan, active plan, nearby shops.
   - **Doctor:** Show table of unchecked plans matching specialization, button to approve/edit.
7. Integrate **Geolocation** for nearby shops.

For exact schema definitions (like what `PlanResponse` looks like), visit `http://127.0.0.1:8000/docs`. Happy coding!
