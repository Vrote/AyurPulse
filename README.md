# AyurPulse — AI-Powered Ayurvedic Wellness Platform 🌿

AyurPulse is a modern, data-driven approach to holistic health. It combines advanced Machine Learning (PyTorch) with ancient Ayurvedic principles to analyze user skin conditions, determine their dominant Prakriti (Dosha balance), and dynamically assemble heavily personalized 7-day treatment plans. 

Additionally, AyurPulse bridges the gap between digital prediction and professional consultation by allowing specialized Ayurvedic Doctors to review, vet, and modify these AI-generated plans via a secure Dashboard.

---

## ⚡ Key Features

*   **AI Skin Diagnostics:** Users upload a face scan, and a deep learning model identifies underlying skin conditions (`acne`, `blackheads`, `wrinkles`, etc.) to trigger a foundational Ayurvedic response.
*   **Prakriti Calculation Engine:** A dynamic 6-question quiz calculates a user's dominant Dosha (`Vata`, `Pitta`, `Kapha`) setting the foundation for all dietary and lifestyle recommendations.
*   **Dynamic Plan Assembly:** Instead of hardcoded text, AyurPulse merges base 7-day plans (`ayurvedic_plans_v2.json`) with an intricate personalization engine (`skin_rules.json`) to adjust routines based on the user's Age, Season, Skin Type, and stress levels dynamically.
*   **Doctor Vetting Dashboard:** Fully secured role-based authentication allowing registered Ayurvedic Doctors to access "Unchecked Plans" filtering only patients relevant to their `specialization`. Doctors can edit, annotate, and verify these plans.
*   **OSM Shop Locator:** Geolocation service mapping the user to nearby physical Ayurvedic stores for ingredient procurement.

---

## 🏗️ Technology Stack

*   **Backend Framework:** FastAPI (Python 3.11+)
*   **Database:** MongoDB Atlas (Async querying via Motor)
*   **AI / Machine Learning:** PyTorch (EfficientNet-B2)
*   **Security:** Stateless JWT Authentication & Bcrypt password hashing
*   **Frontend (Integrating):** React.js

---

## 📖 Contributor Documentation

To ensure a highly scalable and stable deployment, specific documentation guides have been written for team integration. Please read the respective guide before making any changes or pull requests to the repository:

1.  **Frontend Developer Guide:** Read `frontend_requirements.md` for full Swagger-style Endpoint structures, JWT integration rules, and explicit UI workflow assignments.
2.  **Machine Learning / Extensions Guide:** Read `backend_extension_guide.md` to map new AI features (like Hair Analysis or Chatbots) without jeopardizing the existing database stability or Core Prediction Logic.

---

## 🚀 Local Development Setup

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
# Optional: Create a virtual environment
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
*Maintained with ❤️ for the AyurPulse Thesis/Project.*
