"""
plan_controller.py
==================
Generates personalized 7-day Ayurvedic plan.

Real-world flow:
    1. User uploads image → POST /predict → gets prediction_id
    2. User fills 8-field form + passes prediction_id
    3. This controller reads condition from skin_predictions collection
    4. Generates plan → saves to plans collection
    5. Returns 7-day plan with checklists

Collections used:
    skin_predictions  → read condition from here using prediction_id
    plans             → save generated plan here
"""

import json, os, uuid
from datetime import datetime, timezone
from copy import deepcopy

from app.schemas.plan_schema import (
    SkinProfileRequest, PlanResponse,
    DayPlan, ChecklistItem,
)
from app.db.mongodb import get_db

# ── Load datasets once ─────────────────────────────────────────────────────────
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_PLANS    = None
_RULES    = None


def _load():
    global _PLANS, _RULES
    if _PLANS is None:
        plans_path = os.path.join(_DATA_DIR, "ayurvedic_plans_v2.json")
        rules_path = os.path.join(_DATA_DIR, "skin_rules.json")

        if not os.path.exists(plans_path):
            raise FileNotFoundError(f"Missing: {plans_path}")
        if not os.path.exists(rules_path):
            raise FileNotFoundError(f"Missing: {rules_path}")

        with open(plans_path, encoding="utf-8") as f:
            _PLANS = json.load(f)
        with open(rules_path, encoding="utf-8") as f:
            _RULES = json.load(f)
        print("[AyurPulse] Plan datasets loaded")
    return _PLANS, _RULES


# ── Constants ──────────────────────────────────────────────────────────────────
CONDITION_DOSHA = {
    "acne":       "pitta_dominant",
    "blackheads": "kapha_dominant",
    "dark spots": "pitta_dominant",
    "pores":      "kapha_dominant",
    "wrinkles":   "vata_dominant",
}

DOSHA_DISPLAY = {
    "pitta_dominant": "Pitta",
    "kapha_dominant": "Kapha",
    "vata_dominant":  "Vata",
}

DOSHA_TIPS = {
    "pitta_dominant": "Your skin runs hot. Cooling and anti-inflammatory care is your priority.",
    "kapha_dominant": "Your skin produces excess oil. Detox and oil control is your priority.",
    "vata_dominant":  "Your skin is dehydrated. Deep nourishment and moisture is your priority.",
}

DISCLAIMER = (
    "This plan is for general wellness only. "
    "It is not a substitute for professional medical advice. "
    "Consult a dermatologist if your condition is severe or worsening."
)


# ── Resolve condition from latest prediction ───────────────────────────────────
async def _resolve_condition(profile: SkinProfileRequest, user_id: str) -> str:
    """
    Auto-fetch the most recent skin prediction for this user.

    Priority:
        1. Fetch latest from skin_predictions collection (real-world flow)
        2. Fall back to detected_condition if provided (testing/Swagger)

    Returns:
        condition string e.g. "pores", "acne"
    """
    db = get_db()

    # Real world — fetch latest prediction automatically
    if db is not None:
        latest = await db["skin_predictions"].find_one(
            {"user_id": user_id},
            sort=[("created_at", -1)],
            projection={"detected_conditions": 1}
        )
        if latest:
            detected = latest.get("detected_conditions", [])
            if detected:
                return detected[0]   # most recently detected condition

    # Fallback — detected_condition provided directly (Swagger testing)
    if profile.detected_condition:
        return profile.detected_condition

    raise ValueError(
        "No skin analysis found for your account. "
        "Please upload a face image first at POST /api/v1/predict, "
        "then come back to generate your plan."
    )


# ── Step 2: Build checklist ────────────────────────────────────────────────────
def _build_checklist(raw_day: dict, day_num: int,
                     skin_type: str, rules: dict) -> list:
    swaps = rules.get("skin_type", {}).get(skin_type, {}).get("swaps", {})
    items = []
    idx   = 0

    def add(category: str, task: str):
        nonlocal idx
        task = task.strip()
        if not task:
            return
        items.append(ChecklistItem(
            id       = f"d{day_num}_{category}_{idx}",
            category = category,
            task     = task,
            done     = False,
        ))
        idx += 1

    drinks = raw_day.get("diet", {}).get("drinks", [])
    if drinks:
        add("morning", f"Drink: {drinks[0]}")

    for ing in raw_day.get("morning", {}).get("ingredients", [])[:4]:
        safe = swaps.get(ing, ing)
        if safe and safe != "none — skip":
            add("morning", f"Apply: {safe}")

    for step in raw_day.get("morning", {}).get("routine", [])[:3]:
        add("morning", step)

    for ing in raw_day.get("evening", {}).get("ingredients", [])[:4]:
        safe = swaps.get(ing, ing)
        if safe and safe != "none — skip":
            add("evening", f"Apply: {safe}")

    for step in raw_day.get("evening", {}).get("routine", [])[:3]:
        add("evening", step)

    for meal in ["breakfast", "lunch", "dinner"]:
        val = raw_day.get("diet", {}).get(meal, "")
        if val:
            add("diet", f"{meal.capitalize()}: {val}")

    for avoid in raw_day.get("diet", {}).get("avoid", [])[:3]:
        add("diet", f"Avoid: {avoid}")

    yoga = raw_day.get("yoga", "")
    if yoga:
        add("yoga", yoga)

    return items


# ── Step 3: Build tips ─────────────────────────────────────────────────────────
def _build_tips(profile: SkinProfileRequest, rules: dict) -> list:
    tips = []
    age_note   = rules.get("age", {}).get(profile.age_group.value, {}).get("note", "")
    season_tip = rules.get("season", {}).get(profile.season.value, {}).get("tip", "")
    if age_note:   tips.append(age_note)
    if season_tip: tips.append(season_tip)

    lifestyle = rules.get("lifestyle", {})
    if profile.stress_level.value == "high":
        t = lifestyle.get("high_stress", ""); tips.append(t) if t else None
    if profile.sleep_hours.value == "less than 6":
        t = lifestyle.get("poor_sleep", "");  tips.append(t) if t else None
    if profile.water_intake.value == "less than 4 glasses":
        t = lifestyle.get("low_water", "");   tips.append(t) if t else None
    if profile.diet_type.value == "vegan":
        t = lifestyle.get("vegan", "");       tips.append(t) if t else None
    if profile.gender.value == "female":
        t = lifestyle.get("female", "");      tips.append(t) if t else None
    return tips


# ── Main: generate plan ────────────────────────────────────────────────────────
async def generate_plan(
    profile: SkinProfileRequest,
    user_id: str,
) -> PlanResponse:
    """
    Full plan generation flow:
        1. Resolve condition from prediction_id or direct input
        2. Load datasets
        3. Select base plan
        4. Build checklists with skin type swaps
        5. Add personalization tips
        6. Save to MongoDB plans collection
        7. Return clean response
    """
    plans_db, rules = _load()

    # 1. Auto-resolve condition from latest prediction
    condition = await _resolve_condition(profile, user_id)

    # 2. Determine dosha
    dominant_dosha = CONDITION_DOSHA.get(condition, "pitta_dominant")

    # 3. Select base plan
    plans_section = plans_db.get("plans", {})
    condition_key = condition.replace(" ", "_")

    base = (
        plans_section.get(condition_key, {}).get(dominant_dosha) or
        plans_section.get(condition, {}).get(dominant_dosha)
    )

    if not base:
        raise ValueError(
            f"No plan found for condition='{condition}'. "
            f"Available: {list(plans_section.keys())}"
        )

    raw_days = deepcopy(base.get("days", []))
    if not raw_days:
        raise ValueError("Plan has no days. Check ayurvedic_plans_v2.json.")

    # 4. Build tips
    all_tips = _build_tips(profile, rules)

    # 5. Build day plans
    day_plans = []
    for raw in raw_days:
        day_num   = raw["day"]
        checklist = _build_checklist(raw, day_num, profile.skin_type.value, rules)
        tip_parts = [raw.get("tip", "")]
        if day_num == 1 and all_tips:
            tip_parts.extend(all_tips)
        day_plans.append(DayPlan(
            day       = day_num,
            theme     = raw.get("theme", f"Day {day_num}"),
            checklist = checklist,
            tip       = " | ".join([t for t in tip_parts if t]),
        ))

    # 6. Weekly summary
    ws               = base.get("weekly_summary", {})
    key_ingredients  = ws.get("key_ingredients", [])[:6]
    expected_results = ws.get("expected_results", "Follow consistently for best results.")
    diet_changes     = ws.get("key_diet_changes", [])
    weekly_summary   = diet_changes[0] if diet_changes else "Follow checklist daily."

    # 7. Save to MongoDB
    db = get_db()
    plan_doc = {
        "user_id":         user_id,
        "condition":       condition,
        "dominant_dosha":  dominant_dosha,
        "plan_title":      base.get("title", "7-Day Ayurvedic Plan"),
        "profile": {
            "skin_type":    profile.skin_type.value,
            "age_group":    profile.age_group.value,
            "season":       profile.season.value,
            "stress_level": profile.stress_level.value,
            "sleep_hours":  profile.sleep_hours.value,
            "water_intake": profile.water_intake.value,
            "gender":       profile.gender.value,
            "diet_type":    profile.diet_type.value,
        },
        "days":            [d.model_dump() for d in day_plans],
        "key_ingredients": key_ingredients,
        "status":          "active",
        "created_at":      datetime.now(timezone.utc),
    }

    if db is not None:
        result  = await db["plans"].insert_one(plan_doc)
        plan_id = str(result.inserted_id)
    else:
        plan_id = str(uuid.uuid4())

    return PlanResponse(
        status           = "success",
        plan_id          = plan_id,
        condition        = condition,
        dosha            = DOSHA_DISPLAY.get(dominant_dosha, "Pitta"),
        dosha_tip        = DOSHA_TIPS.get(dominant_dosha, ""),
        plan_title       = base.get("title", "7-Day Ayurvedic Plan"),
        key_ingredients  = key_ingredients,
        days             = day_plans,
        weekly_summary   = weekly_summary,
        expected_results = expected_results,
        disclaimer       = DISCLAIMER,
    )


# ── Get saved plan ─────────────────────────────────────────────────────────────
async def get_my_plan(user_id: str) -> dict:
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable.")

    plan = await db["plans"].find_one(
        {"user_id": user_id, "status": "active"},
        sort=[("created_at", -1)]
    )
    if not plan:
        raise ValueError(
            "No active plan found. "
            "Generate a new plan at POST /api/v1/plan/generate."
        )

    plan["plan_id"] = str(plan.pop("_id"))
    return plan