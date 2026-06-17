# AyurPulse — AI-Powered Ayurvedic Wellness Platform 🌿

AyurPulse is a modern, data-driven approach to holistic health. It combines advanced Machine Learning (PyTorch) with ancient Ayurvedic principles to analyze user skin conditions, determine their dominant Prakriti (Dosha balance), and dynamically assemble heavily personalized 7-day treatment plans.

Additionally, AyurPulse bridges the gap between digital prediction and professional consultation by allowing specialized Ayurvedic Doctors to review, vet, and modify these AI-generated plans via a secure Dashboard.

---

## 🧭 Project Documentation Guide Directory

To help you prepare for technical interviews and understand how each component of the full-stack system was engineered, we have split our documentation into highly focused, in-depth technical guides. Click on any link below to explore the architecture and interview focus points:

1. **🧠 [Backend Technical Guide](GUIDE_BACKEND.md):** Deep dive into ASGI (FastAPI), EfficientNet-B2 computer vision inference singletons, Prakriti rules engines, dynamic ingredient swaps, parallel Overpass OSM mirror racing, and custom doctor vetting queue controllers.
2. **🎨 [Frontend Technical Guide](GUIDE_FRONTEND.md):** Deep dive into React SPAs (Vite), global `AuthContext` state, dynamic multi-stage onboarding, state immutability (deep-copying state), and advanced **silent access token refresh** using Axios response interceptors.
3. **🔌 [Full-Stack Integration Guide](GUIDE_INTEGRATION.md):** Comprehensive analysis of E2E patient/doctor communication, CORS middleware, multipart/form file uploading endpoints, and API networks.
4. **🗄️ [Database Technical Guide](GUIDE_DATABASE.md):** Details MongoDB async driver operations (`motor`), document denormalization choices, self-cleaning collections (TTL indexes on blacklisted tokens), and Compound Indexing optimizations.
5. **🧪 [Selenium Testing Guide](GUIDE_SELENIUM_TESTING.md):** Standard-based QA framework including the Page Object Model (POM) design, explicit waiting loops, JS obscured-clicks bypasses, dynamic failure screenshot capturing hooks, and a standalone live-coding script.

---

## ⚡ Key Features

*   **AI Skin Diagnostics:** Users upload a face scan, and a deep learning model identifies underlying skin conditions (`acne`, `blackheads`, `wrinkles`, etc.) to trigger a foundational Ayurvedic response.
*   **Prakriti Calculation Engine:** A dynamic 6-question quiz calculates a user's dominant Dosha (`Vata`, `Pitta`, `Kapha`) setting the foundation for all dietary and lifestyle recommendations.
*   **Dynamic Plan Assembly:** Instead of hardcoded text, AyurPulse merges base 7-day plans (`ayurvedic_plans_v2.json`) with an intricate personalization engine (`skin_rules.json`) to adjust routines based on the user's Age, Season, Skin Type, and stress levels dynamically.
*   **Doctor Vetting Dashboard:** Fully secured role-based authentication allowing registered Ayurvedic Doctors to access "Unchecked Plans" filtering only patients relevant to their `specialization`. Doctors can edit, annotate, and verify these plans.
*   **OSM Shop Locator:** Geolocation service mapping the user to nearby physical Ayurvedic stores for ingredient procurement.

---

## 🚀 Local Development Quickstart

### 1. Requirements
Ensure you have Python 3.11+ and an active MongoDB database (local or Atlas) running.

### 2. Environment Setup
Create a `.env` file in the root directory and add your specific secret keys:
```env
MONGODB_URL=mongodb+srv://<username>:<password>@cluster...
JWT_SECRET_KEY=your_secure_randomly_generated_string
JWT_REFRESH_SECRET_KEY=your_secure_randomly_generated_string
```

### 3. Installation & Run
```bash
# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI Server
python run.py
```

### 4. Interactive API Documentation
Once the server is running, explore and test the entire backend directly via Swagger UI at:
👉 `http://127.0.0.1:8000/docs`

---
*Maintained with ❤️ for the AyurPulse Project.*
