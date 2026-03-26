# AyurPulse Project Progress & Roadmap 🚀

This file is a permanent record of our progress, implementation decisions, and the roadmap for deployment. **Even if our chat history is reset, this file will always remain in your project for reference.**

---

## 🏗️ 1. Project Architecture (Current Status)

*   **Backend**: FastAPI (Python 3.11/12)
*   **Database**: MongoDB (Motor async driver)
*   **AI Model**: PyTorch EfficientNet-B2 (`saved_models/face_skin_disease_model.pth`)
*   **Features Ready**:
    *   ✅ **User Authentication**: Register, Login, Logout, JWT Refresh tokens.
    *   ✅ **Skin Analysis**: Image upload -> AI prediction mapping (Acne, Blackheads, etc.).
    *   ✅ **Shop Locator**: OSM-based nearby Ayurvedic shop search.
    *   ✅ **Data Layer**: Highly detailed Ayurvedic treatment plans (`ayurvedic_plans_v2.json`) and personalization rules (`skin_rules.json`).

---

## 🛠️ 2. Architectural Decisions (New!)

1.  **The "Quick 6" Assessment**: 
    *   To avoid user frustration, we've reduced the Prakriti assessment to the **top 6 most telling questions** (Body Frame, Appetite, Sleep, Skin Temp, Digestion, Personality).
2.  **The Combined User Profile**: 
    *   We will use a single "Smart Consultation Form" that combines:
        *   **Prakriti** (Dosha Score)
        *   **Skin Profile** (Type, Age, Season)
        *   **Lifestyle** (Stress, Water, Diet)

---

## 📅 3. Project Roadmap (Next Steps)

1.  [x] **Step 1: Implementation of the "Smart Assessment" Logic**
    *   ✅ Create `prakriti_assessment.py` (The logic to calculate Dosha scores).
    *   ✅ Create `plan_schema.py` (The data structure for saving profiles).
    *   ✅ **Database Persistence**: Saved plans and profiles to `user_plans` collection.
    *   ✅ **History API**: Added `GET /api/v1/plan/history` endpoint.
2.  [ ] **Step 2: Build the Plan Assembly Engine**
    *   Logic to fetch 7-day plans based on Condition + Dosha.
    *   Logic to apply `skin_rules.json` swaps based on the user's profile.
3.  [ ] **Step 3: End-to-End Testing**
    *   Flow: `Register` -> `Login` -> `Predict (Image)` -> `Complete Profile` -> `Get Plan`.
4.  [ ] **Step 4: Deployment Prep**
    *   Environment variables, CORS config, and Model loading optimization.

---

*Last Updated: 2026-03-25 19:37*
*Note: This file is maintained as your permanent project memory.*
