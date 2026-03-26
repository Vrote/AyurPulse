# AyurPulse Backend Extension Guide (Hair Prediction & Chatbot)

Welcome to the AyurPulse project! Your friend has already built a highly robust, error-free backend system and React frontend guide for **Ayurvedic Skin Condition Plans**. 

Your goal is to extend this project by adding **Hair Problem Prediction** and a **Chatbot**, without breaking or editing the core skin logic. Since the system will be deployed, following this guide strictly ensures the platform remains stable.

---

## 0.5. Existing Endpoint Usage Guide
All APIs are hosted at `http://127.0.0.1:8000/api/v1`. You do not need to build login or user management! You can test all endpoints live at `http://127.0.0.1:8000/docs` (Swagger UI).

### Authentication Endpoints (Already Built!)
- **`POST /auth/register` (Patient):** Creates a standard user.
- **`POST /auth/doctor/register`:** Creates a doctor with a `specialization` dropdown (You must add your Hair specialization here!).
- **`POST /auth/login`:** Returns the `access_token` and `refresh_token`. Your frontend developers will use this to log users in.
- **`POST /auth/refresh`:** Generates a new access token when it expires.
- **`GET /auth/me`:** Pass the token as `Bearer <token>` to get the connected user's details and role (`user` vs `doctor`).

### Core Prediction & Generation Endpoints
- **`POST /predict`:** Uploads an image (`multipart/form-data`) and returns a `prediction_id` identifying the AI result.
- **`GET /plan/questions`:** Returns the dynamic dictionary of UI forms (Dosha assessment + specific options like age/season). 
- **`POST /plan/generate`:** Takes the `prediction_id` and the form answers, calculates Prakriti, and dynamically processes the JSON plans to return a 7-day Ayurvedic routine.

### Patient Dashboards
- **`GET /predict/history`:** Automatically returns all past skin scans for the logged-in user.
- **`GET /plan/history`:** Automatically returns all generated plans for the logged-in user. *(Your hair plans will appear here too!)*
- **`POST /shops/nearby`:** Finds nearby Ayurvedic shops mapping to lat/lng.

### Doctor Dashboards
- **`GET /plan/unchecked-plans`:** Automatically fetches plans needing review, strictly filtering so doctors only see patients matching their `specialization`. *(This means your Hair Doctors will only see Hair Plans!)*
- **`PATCH /plan/{plan_id}/review`:** Saves the doctor's edits and sets `is_doctor_vetted` to `true`.
- **`GET /plan/reviewed-plans`:** Fetches previously reviewed plans.

---

## 1. Creating the Hair Plan JSON Data
Your friend’s system actually uses **TWO** JSON files for the plan generation engine. If you want your Hair Plans to use the same existing plan generation logic, you must create identical structures for both files.

> **General Rule for this Guide:** All the code, JSON, and form examples below are just **structural templates**. You are entirely free to add more options, extra fields, or different hair conditions. Just make sure the *format* (the way dictionaries are nested) exactly mimics these examples!

### File 1: The Master Plans (`hair_plans.json`)
This replaces `ayurvedic_plans_v2.json`. It maps a specific condition and Dosha to a base 7-day Ayurvedic plan.
**Create a new file:** `app/data/hair_plans.json`

### Required JSON Structure for File 1:
```json
{
  "meta": {
    "version": "1.0",
    "description": "Ayurvedic 7-day hair treatment plans",
    "conditions": ["hairfall", "dandruff", "premature_graying"]
  },
  "plans": {
    "hairfall": {
      "pitta_dominant": {
        "plan_id": "HAIRFALL_PITTA",
        "title": "7-Day Pitta-Hairfall Plan",
        "overview": "Cooling plan for heat-driven hair thinning.",
        "dosha_focus": "pitta",
        "days": [
          {
            "day": 1,
            "theme": "Scalp Cooling",
            "morning": {
              "time": "6:00 AM",
              "routine": ["Apply amla oil to scalp"],
              "ingredients": ["amla oil"],
              "procedure": ["1. Massage amla oil gently into scalp for 5 mins."]
            },
            "diet": {
              "breakfast": "Cooling oats",
              "lunch": "Khichdi",
              "dinner": "Light soup",
              "drinks": ["Amla juice"],
              "avoid": ["Chili", "Coffee"]
            },
            "evening": {
              "time": "7:00 PM",
              "routine": ["Wash hair with reetha"],
              "ingredients": ["reetha"],
              "procedure": ["1. Boil reetha and use as natural shampoo."]
            },
            "yoga": "Sheetali Pranayama",
            "tip": "Avoid hot water showers on your head."
          }
          // ... Days 2 through 7
        ],
        "weekly_summary": {
          "key_ingredients": ["amla oil", "reetha"],
          "key_diet_changes": ["reduce heat causing foods"],
          "expected_results": "Reduced hair shed in shower.",
          "continue_after_7_days": "Continue weekly amla oiling."
        }
      }
      // ... kapha_dominant, vata_dominant
    }
    // ... dandruff, premature_graying
  }
}
```

### File 2: The Personalization Rules (`hair_rules.json`)
This replaces `skin_rules.json`. It acts as the logic engine that automatically swaps ingredients or adds tips based on the user's age, season, lifestyle, and **hair type**.

**Create a new file:** `app/data/hair_rules.json`

**Required Structure for File 2:**
```json
{
  "hair_type": {
    "oily": {
      "note": "Avoid heavy coconut oil, use aloe vera",
      "swaps": {
        "coconut oil": "aloe vera gel"
      }
    },
    "dry": { "note": "...", "swaps": {} }
  },
  "age": {
    "21-30": { "note": "Start scaling scalp massages." }
  },
  "season": {
    "summer": { "tip": "Use cooling essential oils." }
  },
  "lifestyle": {
    "high_stress": "Stress increases hair shedding. Practice Brahmari."
  }
}
```
**How it works:** When you build the `hair_controller.py`, you will parse this file and use the `swaps` dictionary to dynamically replace string ingredients in the 7-day master plan before returning it to the user.

---

## 2. File Architecture (Do NOT edit Skin files)
To avoid breaking the deployment, create **new files** for your specific endpoints instead of polluting the existing skin routes.

### Create these new files:
1. `app/schemas/hair_schema.py` (Define your hair prediction request/response models)
2. `app/controllers/hair_controller.py` (Write your AI prediction logic here)
3. `app/routes/hair_routes.py` (Create a simple FastAPI router: `router = APIRouter(prefix="/api/v1/hair")`)
4. `app/routes/chatbot_routes.py` (Create your Chatbot endpoints here)

### Registering your routes safely:
Go to `app/main.py`. Under the existing router inclusions, add yours:
```python
from app.routes.hair_routes import router as hair_router
from app.routes.chatbot_routes import router as chatbot_router

# Inside create_app():
app.include_router(hair_router)
app.include_router(chatbot_router)
```

---

## 3. The Hair Assessment Questions Engine
Your friend's logic uses a unified form endpoint returning exact string options to the React developer. 

**You must build the exact same UI payload generator for Hair!**
Create a new file `app/utils/hair_assessment.py`. This file must define every possible option a patient can select for their hair profile, which you must also strictly validate in your `app/schemas/hair_schema.py` using Pydantic.

**Example Setup for your options:**
```python
def get_hair_questions():
    return {
        "unified_form": [
             # Dosha Questions (Keep these exactly the same)
             { "id": "body_frame", "options": [{"value": "small_thin", "text": "Small/Thin"}] },
             
             # Your Custom Hair Variables
             {
                 "section": "2. Hair Profile",
                 "id": "hair_type",
                 "type": "select",
                 "options": [
                     {"value": "dry_frizzy", "text": "Dry & Frizzy"},
                     {"value": "oily_thin", "text": "Oily & Thinning"},
                     {"value": "thick_greasy", "text": "Thick & Greasy"}
                 ]
             },
             {
                 "section": "3. Scalp Health",
                 "id": "scalp_issue",
                 "type": "select",
                 "options": [
                     {"value": "flaky_white", "text": "Dry White Flakes"},
                     {"value": "yellow_crust", "text": "Yellow Oily Crusts"},
                     {"value": "normal_scalp", "text": "Normal"}
                 ]
             }
        ]
    }
```
**CRITICAL:** Every single string option (`"dry_frizzy"`, `"flaky_white"`) you define here must exactly match the keys written in your `hair_rules.json` file. No free-text allowed!

---

## 4. Extending the Doctor Feature for Hair 
Your friend implemented a feature where AI plans are routed to specific doctors based on their **Specialization**. 

To allow doctors to specialize in Hair, you need to update a few existing places:

### A. Update the Frontend Registration Dropdown:
In the Doctor Registration form, doctors **must** select their specialization from a strict Dropdown menu. **They cannot be allowed to type free-text specializations!** If they randomly type strings with typos, the routing logic fails and they will never receive plans in their dashboard.
- Inform the frontend developer to add your exact new hair specialization to the registration dropdown list.
- Recommended exact addition: `"Ayurvedic Trichology"`

### B. Update the Backend Routing Logic:
Open `app/controllers/plan_controller.py` (or create a `hair_plan_controller.py` clone). 
Look for the `condition_to_specialty` dictionary. Add your hair conditions mapping to your new Doctor Specialization so the routing system knows where to send the hair plans:

```python
condition_to_specialty = {
    # Existing Skin Conditions (Do NOT touch)
    "acne": "Ayurvedic Dermatology",
    "blackheads": "Ayurvedic Dermatology",
    "dark_spots": "Skin Rejuvenation",
    "pores": "Ayurvedic Dermatology",
    "wrinkles": "Anti-Aging (Rasayana)",
    
    # YOUR NEW HAIR CONDITIONS
    "hairfall": "Ayurvedic Trichology",
    "dandruff": "Ayurvedic Trichology",
    "premature_graying": "Ayurvedic Trichology"
}
```
**How this works:** When a patient generates a plan for `hairfall`, the backend flags it as requiring `Ayurvedic Trichology`. Only Doctors who registered with the `Ayurvedic Trichology` specialization (or `General Ayurveda`) will see this patient's plan in their "Unchecked Plans" dashboard list!

---

## 5. Chatbot Guidelines
- When building the chatbot (`app/routes/chatbot_routes.py`), ensure it only returns Ayurvedic advice.
- Protect your chatbot endpoint with the existing `Depends(get_current_user)` middleware function from `app.auth.dependencies` so that only logged-in users can use the chatbot.
- **Tip:** You can fetch the user's previously generated plans or Dosha results from the MongoDB `user_plans` collection and pass it as context to your LLM (OpenAI/Gemini) so the chatbot gives highly personalized Ayurvedic advice rather than generic answers.

---

## 6. Using the Existing Authentication and Database
Your friend has already fully built the User Authentication system and the MongoDB connection engine. **Do not create new login systems, new JWT logic, or separate databases!**

### A. Securing your New Hair/Chatbot Endpoints:
To make sure a user is logged in before they generate a Hair Plan or use the Chatbot, simply import and inject the existing dependency into your FastAPI routes:
```python
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/hair")

@router.post("/predict")
async def predict_hair(current_user: dict = Depends(get_current_user)):
    user_id = current_user["user_id"] # Backend parses this from their secure token!
    return {"message": "You are verified!", "user_id": user_id}
```

### B. Accessing the Database:
Avoid writing custom PyMongo clients or connection strings. Use the global MongoDB connection state already set up in the app.
Whenever your specific hair logic needs to save a plan or fetch data, just do:
```python
from app.db.mongodb import get_db

async def save_hair_plan(plan_data):
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable")
    
    # Excellent tip: Save the new hair plan into the EXACT SAME "user_plans" collection
    await db["user_plans"].insert_one(plan_data)
```
**Why?** By saving your nested hair plans into the existing `user_plans` collection alongside the skin plans, the existing Doctor's Dashboard feature (which fetches from `user_plans`) will naturally pick up all your hair plans. You won't have to build a whole second dashboard UI!

Follow these structural splits and the platform will merge beautifully for deployment! Happy coding!
