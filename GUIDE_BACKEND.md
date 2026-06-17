# 🧠 AyurPulse Backend Technical Guide: Interview Perspective

This document serves as the comprehensive source of truth for the **AyurPulse** backend system. It covers the core architecture, AI diagnostics pipeline, dynamic rule engines, geolocation workflows, API route structures, and intermediate-to-advanced interview preparation questions.

---

## 🏛️ 1. Technical Stack & Architecture Overview

The backend is built as a high-performance, asynchronous REST API using:
*   **FastAPI:** Modern Python web framework leveraging ASGI (Asynchronous Server Gateway Interface) instead of WSGI (like Flask/Django) for concurrent request handling.
*   **PyTorch & torchvision:** Serves fine-tuned **EfficientNet-B2** computer vision model weights.
*   **MongoDB & Motor:** Fully asynchronous MongoDB driver matching FastAPI's non-blocking runtime.
*   **Pydantic (v2):** Fast data serialization, input sanitation, and automated OpenAPI documentation.

### ⚙️ System Routing & Directories
```text
Ayurpulse/app/
├── config/         # App settings & Pydantic environment configurations
├── controllers/    # Core business logic (AI, Rules Engine, Geolocations)
├── db/             # Async Motor connection & collection indexes
├── models/         # PyTorch singleton architecture and loader
├── routes/         # API endpoints divided by routers (Auth, Plan, Shops)
├── schemas/        # Request/Response data validation schemas
└── utils/          # Auxiliary helper modules (Prakriti, Image processing, Logger)
```

---

## 🧬 2. Core Features & Technical Workflows

### 2.1. AI Diagnostics Engine (Computer Vision Pipeline)
*   **Architecture:** Fine-tuned **EfficientNet-B2** model targeting 5 facial skin conditions: `acne`, `blackheads`, `dark spots`, `pores`, `wrinkles`.
*   **Singleton Pattern:** Loading deep learning models in memory takes 2–5 seconds and consumes significant RAM. To prevent this overhead on every request, the model is loaded as a **Singleton** on startup in `app/models/prediction_model.py`.
*   **Dynamic Device Selection:** Automatically runs on **CUDA (GPU)** if available, falling back to **CPU** in containerized or local development environments.
*   **Image Processing Pipeline (`app/utils/image_preprocess.py`):**
    1.  **Format Handling:** Converts raw input bytes to an RGB PIL Image (ensuring transparent PNGs or grayscale JPEGs do not crash the tensor conversion).
    2.  **Resizing:** Scales the image down to $224 \times 224$ pixels matching the EfficientNet-B2 input layer.
    3.  **Normalization:** Standardizes pixel intensities using ImageNet parameters: `mean=[0.485, 0.456, 0.406]` and `std=[0.229, 0.224, 0.225]`.
    4.  **Batch Dimension:** Adds the batch dimension via `unsqueeze(0)` to transform the tensor shape from `(3, 224, 224)` to `(1, 3, 224, 224)`.
*   **Dynamic Thresholding Logic:** Instead of returning a forced prediction (like standard classifiers), we apply customized thresholds on the softmax output to prevent false positives:
    *   `acne`, `blackheads`, `pores`, `dark_spots`: **88.0%** threshold.
    *   `wrinkles`: **96.0%** threshold (prevents normal laugh lines from being flagged).

```python
# Technical snapshot from prediction_controller.py
model, device = load_model()
tensor = tensor.to(device)

with torch.no_grad():  # Crucial for saving memory and disabling backpropagation tracking
    outputs = model(tensor)
    probs = F.softmax(outputs, dim=1)

prob_values = probs[0].cpu().numpy() * 100

# Apply class-specific threshold filtering
detected_conditions = [
    cls for cls, prob in zip(CLASS_NAMES, prob_values)
    if prob >= get_threshold(cls)
]
```

### 2.2. Prakriti Quiz & Dynamic Plan Assembly (Rule Engine)
After diagnosing the skin condition, patients answer a **6-question Prakriti Quiz** analyzing frame size, hunger levels, sleep patterns, etc.
*   **Dominance Calculation:** The `calculate_dosha()` function tally-counts answer responses mapping to `Vata`, `Pitta`, and `Kapha`. The dosha with the highest frequency is declared the patient's dominant Prakriti.
*   **Dynamic Splicing Mechanism (`app/controllers/plan_controller.py`):**
    1.  **Retrieval:** Loads base 7-day schedules from `ayurvedic_plans_v2.json` matching `[detected_condition][dominant_dosha]`.
    2.  **Ingredient Swaps:** Queries `skin_rules.json` to modify the plan dynamically according to patient attributes. For instance, if a patient has **oily skin**, standard heavy oils are dynamically swapped (e.g., *"coconut oil"* $\rightarrow$ *"aloe vera gel"* or *"jojoba oil"*).
    3.  **Personalization:** Splices custom `personalization_notes` depending on the patient's age bracket, current season tips, and lifestyle factors (e.g., warning indicators for stress or poor sleep).
    4.  **Persistence:** Saves the plan in the database in an **unvetted state** (`is_doctor_vetted = False`) and routes it to the specific medical specialty queue.

### 2.3. Doctor Specialization-Based Routing & Vetting
Plans require verification by an Ayurvedic doctor matching the specialization of the diagnosed skin condition:
*   `acne` / `blackheads` / `pores` $\rightarrow$ `Ayurvedic Dermatology`
*   `dark_spots` $\rightarrow$ `Skin Rejuvenation`
*   `wrinkles` $\rightarrow$ `Anti-Aging (Rasayana)`

#### ⚠️ The Critical Vetting Override Bug & Fix:
*   **The Bug:** In early releases, when doctors vetted or modified a plan via `PATCH /plan/{plan_id}/review`, the backend directly merged the payload: `update_data.update(request.modified_plan)`. Because the `modified_plan` payload was a cloned copy from the client UI, it contained `"is_doctor_vetted": false`, which silently overwrote the doctor's vetting confirmation flag back to `false` in the database, locking the plan in the unchecked queue.
*   **The Fix:** We implemented a strict **Sensitive Data Cleanup** filter in `plan_controller.py` that strips structural state flags, user IDs, and metadata before merging updates into the database:

```python
# Strip keys that the doctor shouldn't modify directly in nested fields
forbidden_keys = [
    "id", "_id", "user_id", "prediction_id", "created_at",
    "is_doctor_vetted", "is_doctor_modified", "doctor_notes", "doctor_name", "reviewed_at",
    "patient_metadata"
]
for key in forbidden_keys:
    if key in request.modified_plan:
        del request.modified_plan[key]

# Safely merge updates
update_data.update(request.modified_plan)
```

### 2.4. Geolocation Search (OSM Overpass Parallel API)
*   **Mechanism:** Searches nearby Ayurvedic pharmacies using GPS coordinates (`POST /shops/nearby`).
*   **Parallel Mirror Racing:** To eliminate latency and OSM Overpass server timeouts (which throw 503 errors), the backend queries **4 global Overpass mirrors in parallel** using a thread pool. The first mirror to reply successfully wins, and all remaining pending tasks are immediately cancelled (`asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`).
*   **Iterative Expansion:** Starts searching with a small radius of **5km**. If fewer than **3 matching shops** are found, it automatically expands the search radius sequentially to **10km, 15km, 20km, and 30km** to guarantee results in remote areas.
*   **Distance Calculation:** Computes distances between the patient's coordinates and shops using the **Haversine formula**.

---

## 💡 3. Interview Focus: Common Backend Questions & Answers

#### Q1: Why did you choose FastAPI over Django or Flask?
**A:** FastAPI is built natively on ASGI (Asynchronous Server Gateway Interface), making it significantly faster at handling non-blocking concurrent requests. Unlike WSGI frameworks (like Flask or Django) which block a thread per request, FastAPI uses an event loop (via `uvicorn`) that yields control during slow I/O tasks—such as querying external Overpass geolocation APIs or reading from MongoDB. Additionally, it offers native asynchronous support, Pydantic type safety, and auto-generated OpenAPI documentation.

#### Q2: What is the benefit of loading your PyTorch model as a Singleton?
**A:** Loading deep learning models in memory requires parsing model architectures and loading heavy weight matrices (tensors) from disk, consuming considerable CPU and RAM (taking 2–5 seconds). If done on every API request, the server would experience massive latency spikes and quickly crash due to memory saturation. Loading it as a **Singleton** ensures the weights are loaded into RAM **once** when the server boots, allowing subsequent API request inferences to run in milliseconds.

#### Q3: How do you prevent SQL/NoSQL Injection in your backend?
**A:** We use **Pydantic schemas** to enforce strict type-checking on all request payloads. Pydantic validates types (e.g. enforcing that coordinates are floats and strings match format requirements) before payloads ever reach controller logic. For database operations, MongoDB's async driver (`motor`) uses parametrized queries instead of raw string concatenations, neutralizing NoSQL injection risks.

#### Q4: How does your parallel OSM Overpass queries racing improve system reliability?
**A:** OpenStreetMap Overpass servers are public, free-to-use mirrors that suffer from frequent rate-limiting, slow response times, and intermittent downtime. A single server call could block for up to 50 seconds or throw 503 gateway errors. By querying 4 independent mirrors concurrently, we leverage server redundancy: if 3 servers are down or slow, the 4th healthy mirror returns the result in under a second, shielding the patient from system failures.
