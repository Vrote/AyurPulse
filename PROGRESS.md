# AyurPulse Project Progress & Roadmap 🚀

This file is a permanent record of our progress, architecture decisions, and current deployment state. **This file serves as the master overview of what has been accomplished in this project.**

---

## 🏗️ 1. Project Architecture (Current Status)

*   **Backend**: FastAPI (Python 3.11/12)
*   **Database**: MongoDB (Motor async driver)
*   **AI Model**: PyTorch EfficientNet-B2
*   **Authentication**: JWT-based stateless auth for distinct `user` and `doctor` roles.

### ✅ Completed Modules:
*   **User Registration & Authentication**: Full JWT lifecycle, robust Bcrypt hashing, session refresh logic.
*   **Doctor Authentication & Vetting System**: Custom doctor registration requiring strict specializations. Doctors have isolated dashboards where they view unfiltered AI plans (`unchecked-plans`) that match their expertise and submit `doctor_notes` directly modifying patient history (`reviewed-plans`).
*   **Skin Analysis Integration**: Endpoint linking raw multipart image uploads to backend PyTorch prediction thresholds safely triggering Ayurvedic logic.
*   **Prakriti Engine**: 6-question robust algorithm determining dominant Doshas based strictly mapped string values.
*   **Plan Assembly Engine**: Heavy dynamic algorithm joining `ayurvedic_plans_v2.json` (7-day base plans) with `skin_rules.json` (Personalization rules for age, season, and lifestyle swaps).
*   **OSM Shops**: Geolocation matching users to local Ayurvedic stores.

---

## 📝 2. External Developer Integration Rules

With the core Skin analysis backend fully complete, the project is configured to receive expansions from group mates:

1.  **Frontend Developer (React)**:
    *   **Resource File:** `frontend_requirements.md`
    *   **Status:** The guide is fully generated. It explicitly outlines every endpoint, Authentication token requirement, and how the React state should manage Data (e.g., Doctors editing plans via the `PATCH` endpoint, or Users seeing "Verified" checkmarks once a plan is checked).

2.  **Hair Prediction & Chatbot Expansion (Python/AI Developer)**:
    *   **Resource File:** `backend_extension_guide.md`
    *   **Status:** A strict rule guide was created to ensure the secondary backend developer securely extends the project without breaking existing routing logic. She is strictly tasked to create alternative files (e.g., `hair_plans.json`, `hair_routes.py`) and loop to the same MongoDB `user_plans` connection.

---

## 📅 3. Pipeline & Deployment (Next Steps)

1.  [x] **Step 1: AI Plan Engine Consolidation** (Done)
2.  [x] **Step 2: Doctor Dashboard Logic & Permissions** (Done)
3.  [x] **Step 3: Frontend Schema Rules & Documentation** (Done)
4.  [x] **Step 4: Extension Groupmate Documentation** (Done)
5.  [ ] **Step 5: Frontend Integration Execution**
    *   Hand off `frontend_requirements.md` to the React developer.
    *   Test End-to-End CORS compatibility with React `localhost:3000`.
6.  [ ] **Step 6: Chatbot & Hair Extension Execution**
    *   Secondary developer creates `hair_plans.json` and hooks the `Ayurvedic Trichology` specialization logic inline.
7.  [ ] **Step 7: Production Deployment Process**
    *   MongoDB Atlas production migration.
    *   Uvicorn production execution on rendering service (Render/Heroku/AWS).

---

*Last Updated: 2026-03-27*
*Note: This file is maintained as your permanent project memory.*
