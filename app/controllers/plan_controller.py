import json
import os
from typing import Dict, List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from datetime import datetime
from app.utils.logger import logger

from app.db.mongodb import get_db
from app.controllers.rag_controller import generate_rag_plan
from app.utils.prakriti_assessment import calculate_dosha
from app.schemas.plan_schema import PlanRequest, PlanResponse, DayPlan, WeeklySummary, RoutineStep, DietPlan, PlanReviewRequest, PatientMetadata


def load_json_data(filename: str) -> Dict:
    """Helper to load JSON data from the data/ folder."""
    path = os.path.join("app", "data", filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def generate_personalized_plan(request: PlanRequest, user_id: str) -> PlanResponse:
    """
    The Brain of the Plan System:
    Connects Prediction -> Dosha -> Rule-based personalization.
    """
    
    # 1. Fetch AI Prediction from MongoDB
    db = get_db()
    if db is None:
        logger.error("DB connection unavailable for this task.")
        raise RuntimeError("Database connection failed.")

    prediction = await db["skin_predictions"].find_one({"_id": ObjectId(request.prediction_id)})
    if not prediction:
        raise ValueError(f"No prediction found with ID {request.prediction_id}")

    # Pick the primary condition (if empty, default to acne as a fallback or raise error)
    detected = prediction.get("detected_conditions", [])
    if not detected:
        condition = "acne" # Fallback if user wants a plan anyway
    else:
        condition = detected[0].lower().replace(" ", "_") # Normalize format (e.g. "dark_spots")

    # 2. Determine Dominant Dosha from answers
    dominant_dosha = calculate_dosha(request.dosha_answers.model_dump())

    # 2.1 Fetch patient details and construct PatientMetadata
    patient_name = "Anonymous Patient"
    try:
        user_doc = await db["users"].find_one({"_id": ObjectId(user_id)})
        if user_doc:
            patient_name = user_doc.get("full_name", "Anonymous Patient")
    except Exception as e:
        logger.error(f"Failed to fetch user full name in plan generation: {e}")

    patient_metadata = PatientMetadata(
        full_name=patient_name,
        age_group=request.age_group,
        skin_type=request.skin_type,
        lifestyle=request.lifestyle,
        dosha_answers=request.dosha_answers.model_dump()
    )

    # 2.5 RAG-Enhanced Plan Generation (try before rule-based fallback)
    try:
        lifestyle_data = {
            "sleep_hours": "poor" if "poor_sleep" in request.lifestyle else "normal",
            "stress_level": "high" if "high_stress" in request.lifestyle else "normal",
            "water_intake": "low" if "low_water" in request.lifestyle else "normal",
            "exercise_frequency": "unknown"
        }
        rag_plan = await generate_rag_plan(
            condition=condition,
            dominant_dosha=dominant_dosha,
            age=request.age_group,
            lifestyle_data=lifestyle_data
        )
        if rag_plan is not None:
            logger.info("RAG plan generated successfully for user")

            # Determine required specialty
            condition_to_specialty_rag = {
                "acne": "Ayurvedic Dermatology",
                "blackheads": "Ayurvedic Dermatology",
                "dark_spots": "Skin Rejuvenation",
                "pores": "Ayurvedic Dermatology",
                "wrinkles": "Anti-Aging (Rasayana)"
            }
            required_specialty = condition_to_specialty_rag.get(condition, "General Ayurveda")

            # Build PlanResponse from RAG plan dict
            rag_days = []
            for day_data in rag_plan.get("days", []):
                morning = RoutineStep(
                    time=day_data.get("morning", {}).get("time", "6:00 AM"),
                    routine=day_data.get("morning", {}).get("routine", []),
                    ingredients=day_data.get("morning", {}).get("ingredients", []),
                    procedure=day_data.get("morning", {}).get("procedure", [])
                )
                evening = RoutineStep(
                    time=day_data.get("evening", {}).get("time", "7:00 PM"),
                    routine=day_data.get("evening", {}).get("routine", []),
                    ingredients=day_data.get("evening", {}).get("ingredients", []),
                    procedure=day_data.get("evening", {}).get("procedure", [])
                )
                diet = DietPlan(
                    breakfast=day_data.get("diet", {}).get("breakfast", ""),
                    lunch=day_data.get("diet", {}).get("lunch", ""),
                    dinner=day_data.get("diet", {}).get("dinner", ""),
                    drinks=day_data.get("diet", {}).get("drinks", []),
                    avoid=day_data.get("diet", {}).get("avoid", [])
                )
                rag_days.append(DayPlan(
                    day=day_data.get("day", 1),
                    theme=day_data.get("theme", ""),
                    morning=morning,
                    diet=diet,
                    evening=evening,
                    yoga=day_data.get("yoga", ""),
                    tip=day_data.get("tip", "")
                ))

            ws = rag_plan.get("weekly_summary", {})
            weekly_summary = WeeklySummary(
                key_ingredients=ws.get("key_ingredients", []),
                key_diet_changes=ws.get("key_diet_changes", []),
                expected_results=ws.get("expected_results", ""),
                continue_after_7_days=ws.get("continue_after_7_days", "")
            )

            response = PlanResponse(
                plan_id=rag_plan.get("plan_id", f"{condition}_{dominant_dosha}_RAG"),
                title=rag_plan.get("title", ""),
                overview=rag_plan.get("overview", ""),
                dosha_focus=rag_plan.get("dosha_focus", dominant_dosha.replace("_dominant", "")),
                required_specialty=required_specialty,
                personalization_notes=[f"RAG-personalized plan for {condition} ({dominant_dosha})"],
                days=rag_days,
                weekly_summary=weekly_summary,
                is_doctor_vetted=False,
                is_doctor_modified=False,
                doctor_notes=None,
                doctor_name=None,
                reviewed_at=None,
                created_at=datetime.now().isoformat(),
                patient_metadata=patient_metadata
            )

            # Save to MongoDB
            if db is not None:
                plan_doc = response.model_dump()
                plan_doc["user_id"] = user_id
                plan_doc["prediction_id"] = request.prediction_id
                plan_doc["created_at"] = datetime.now()
                result = await db["user_plans"].insert_one(plan_doc)
                response.id = str(result.inserted_id)

            return response
        else:
            logger.info("RAG returned None, using rule-based fallback")
    except Exception as e:
        logger.error(f"RAG pipeline error in plan_controller: {e}")

    # 3. Load Master Plans and Skin Rules (Rule-Based Fallback)
    master_plans = load_json_data("ayurvedic_plans_v2.json")
    skin_rules   = load_json_data("skin_rules.json")

    # Check if plan exists for this condition and dosha
    if condition not in master_plans["plans"]:
        condition = "acne" # Fallback to acne if specific condition plan doesn't exist yet
    
    base_plan = master_plans["plans"][condition][dominant_dosha]

    # 4. Personalization Logic (Rule Engine)
    personalization_notes = []
    
    # Get Swaps for this Specific Skin Type
    skin_rules_data = skin_rules.get("skin_type", {}).get(request.skin_type, {})
    swaps = skin_rules_data.get("swaps", {})
    if skin_rules_data.get("note"):
        personalization_notes.append(skin_rules_data["note"])

    # Age specific note
    age_note = skin_rules.get("age", {}).get(request.age_group, {}).get("note")
    if age_note:
        personalization_notes.append(age_note)

    # Season specific tip
    season_tip = skin_rules.get("season", {}).get(request.season, {}).get("tip")
    if season_tip:
        personalization_notes.append(f"Season Tip ({request.season.capitalize()}): {season_tip}")

    # Lifestyle notes
    for factor in request.lifestyle:
        lifestyle_note = skin_rules.get("lifestyle", {}).get(factor)
        if lifestyle_note:
            personalization_notes.append(lifestyle_note)

    # 5. Apply Object Manipulation (The Swaps)
    # We will iterate through each day and swap ingredients/routines based on skin type
    processed_days = []
    
    for day_data in base_plan["days"]:
        # Helper to apply swaps to a list of strings
        def apply_swaps_to_list(items: List[str]) -> List[str]:
            new_items = []
            for item in items:
                new_item = item.lower()
                for old, new in swaps.items():
                    if old in new_item:
                        new_item = new_item.replace(old, new)
                new_items.append(new_item.capitalize())
            return new_items

        # Apply to Morning, Diet, Evening
        morning = RoutineStep(
            time        = day_data["morning"]["time"],
            routine     = apply_swaps_to_list(day_data["morning"]["routine"]),
            ingredients = apply_swaps_to_list(day_data["morning"]["ingredients"]),
            procedure   = apply_swaps_to_list(day_data["morning"].get("procedure", []))
        )
        
        evening = RoutineStep(
            time        = day_data["evening"]["time"],
            routine     = apply_swaps_to_list(day_data["evening"]["routine"]),
            ingredients = apply_swaps_to_list(day_data["evening"]["ingredients"]),
            procedure   = apply_swaps_to_list(day_data["evening"].get("procedure", []))
        )
        
        diet = DietPlan(
            breakfast = day_data["diet"]["breakfast"],
            lunch     = day_data["diet"]["lunch"],
            dinner    = day_data["diet"]["dinner"],
            drinks    = day_data["diet"]["drinks"],
            avoid     = day_data["diet"]["avoid"]
        )

        processed_days.append(DayPlan(
            day     = day_data["day"],
            theme   = day_data["theme"],
            morning = morning,
            diet    = diet,
            evening = evening,
            yoga    = day_data["yoga"],
            tip     = day_data["tip"]
        ))

    # Prepare Weekly Summary
    summary_data = base_plan["weekly_summary"]
    weekly_summary = WeeklySummary(
        key_ingredients        = apply_swaps_to_list(summary_data["key_ingredients"]),
        key_diet_changes       = summary_data["key_diet_changes"],
        expected_results       = summary_data["expected_results"],
        continue_after_7_days  = summary_data["continue_after_7_days"]
    )

    # Determine required specialty based on condition
    condition_to_specialty = {
        "acne": "Ayurvedic Dermatology",
        "blackheads": "Ayurvedic Dermatology",
        "dark_spots": "Skin Rejuvenation",
        "pores": "Ayurvedic Dermatology",
        "wrinkles": "Anti-Aging (Rasayana)"
    }
    required_specialty = condition_to_specialty.get(condition, "General Ayurveda")

    # 6. Build Final Response Object
    response = PlanResponse(
        plan_id               = base_plan["plan_id"],
        title                 = base_plan["title"],
        overview              = base_plan["overview"],
        dosha_focus           = base_plan["dosha_focus"],
        required_specialty    = required_specialty,
        personalization_notes = personalization_notes,
        days                  = processed_days,
        weekly_summary        = weekly_summary,
        is_doctor_vetted      = False,
        is_doctor_modified    = False,
        doctor_notes          = None,
        doctor_name           = None,
        reviewed_at           = None,
        created_at            = datetime.now().isoformat(),
        patient_metadata      = patient_metadata
    )

    # 7. Save to MongoDB user_plans collection (Persistence)
    if db is not None:
        plan_doc = response.model_dump()
        plan_doc["user_id"]       = user_id
        plan_doc["prediction_id"] = request.prediction_id
        plan_doc["created_at"]    = datetime.now() # Store as datetime object in DB
        
        result = await db["user_plans"].insert_one(plan_doc)
        response.id = str(result.inserted_id)



    return response


async def get_plan_history(user_id: str):
    """Fetch user's last 5 generated plans."""
    db = get_db()
    if db is None:
        return []

    cursor = db["user_plans"].find(
        {"user_id": user_id},
        {"_id": 0} # Exclude internal ID
    ).sort("created_at", -1).limit(5)

    history = []
    async for doc in cursor:
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("reviewed_at"), datetime):
            doc["reviewed_at"] = doc["reviewed_at"].isoformat()
        history.append(doc)
    
    return history


async def _backfill_patient_metadata(doc: dict, db) -> dict:
    """Helper to backfill patient_metadata for old database records."""
    if not doc.get("patient_metadata"):
        try:
            p_name = "Anonymous Patient"
            if "user_id" in doc:
                user_doc = await db["users"].find_one({"_id": ObjectId(doc["user_id"])})
                if user_doc:
                    p_name = user_doc.get("full_name", "Anonymous Patient")
            
            # Use general default fallback details for old records
            doc["patient_metadata"] = {
                "full_name": p_name,
                "age_group": "21-30",
                "skin_type": "combination",
                "lifestyle": [],
                "dosha_answers": {
                    "body_frame": "medium",
                    "hunger": "very_strong",
                    "sleep": "sound",
                    "feeling": "hot",
                    "digestion": "burning",
                    "mood": "focused_irritable"
                }
            }
        except Exception as e:
            logger.error(f"Failed to backfill patient_metadata: {e}")
    return doc


async def get_all_plans_for_doctor(specialization: Optional[str] = None):
    """
    Fetch all plans for doctor to review (most recent first).
    Optionally filters by the doctor's specialization.
    """
    db = get_db()
    if db is None:
        return []

    # Filtering logic: General Ayurveda sees EVERYTHING. Specialists see their field + general.
    query = {"is_doctor_vetted": False}
    
    # If the doctor is NOT a Generalist, we restrict their view to their specialty + general items
    if specialization and specialization != "General Ayurveda":
        query["$or"] = [
            {"required_specialty": specialization},
            {"required_specialty": "General Ayurveda"},
            {"required_specialty": {"$exists": False}} # Support older plans
        ]

    cursor = db["user_plans"].find(query).sort("created_at", -1)
    
    plans = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        # Format timestamps
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("reviewed_at"), datetime):
            doc["reviewed_at"] = doc["reviewed_at"].isoformat()
        # Backfill
        doc = await _backfill_patient_metadata(doc, db)
        plans.append(doc)
    
    return plans


async def get_reviewed_plans_for_doctor(specialization: Optional[str] = None):
    """
    Fetch all plans that have already been reviewed/checked by a doctor.
    Shows the history of patient reviews and modifications.
    """
    db = get_db()
    if db is None:
        return []

    # Filtering logic: Only vetted plans, filtered by specialty
    query = {"is_doctor_vetted": True}
    if specialization and specialization != "General Ayurveda":
        query["$or"] = [
            {"required_specialty": specialization},
            {"required_specialty": "General Ayurveda"}
        ]

    cursor = db["user_plans"].find(query).sort("reviewed_at", -1)
    
    plans = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        # Format timestamps
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        if isinstance(doc.get("reviewed_at"), datetime):
            doc["reviewed_at"] = doc["reviewed_at"].isoformat()
        # Backfill
        doc = await _backfill_patient_metadata(doc, db)
        plans.append(doc)
    
    return plans


async def review_plan_by_doctor(plan_id: str, request: PlanReviewRequest, doctor_name: str):
    """Allow doctor to approve or modify a user's plan."""
    db = get_db()
    if db is None:
        logger.error("DB connection unavailable for this task.")
        raise RuntimeError("Database connection failed.")

    # 1. Check if plan exists (protect against invalid ObjectId strings)
    try:
        obj_id = ObjectId(plan_id)
    except InvalidId:
        raise ValueError(f"Invalid Plan ID format: '{plan_id}'. Please use the 24-character hex ID from the 'all plans' list.")

    existing_plan = await db["user_plans"].find_one({"_id": obj_id})
    if not existing_plan:
        raise ValueError(f"Plan with ID '{plan_id}' not found in high-priority vetting queue.")

    # 2. Update logic
    update_data = {
        "is_doctor_vetted": request.is_doctor_vetted,
        "is_doctor_modified": False, # Default
        "doctor_notes": request.doctor_notes,
        "doctor_name": doctor_name,
        "reviewed_at": datetime.now()
    }

    # If the doctor provided a fully modified plan, merge it
    if request.modified_plan:
        update_data["is_doctor_modified"] = True
        # ── SENSITIVE DATA CLEANUP ──
        # Strictly prevent doctor from changing internal system/user IDs
        forbidden_keys = ["id", "_id", "user_id", "prediction_id", "created_at", "is_doctor_vetted", "is_doctor_modified", "doctor_notes", "doctor_name", "reviewed_at"]
        for key in forbidden_keys:
            if key in request.modified_plan:
                del request.modified_plan[key]
        
        # Merge safely cleaned modified plan into update_data
        update_data.update(request.modified_plan)
        logger.info(f"Doctor '{doctor_name}' modified content for plan {plan_id}")
    else:
        logger.info(f"Doctor '{doctor_name}' vetted plan {plan_id} without modifications.")

    # 3. Save updates
    await db["user_plans"].update_one(
        {"_id": obj_id},
        {"$set": update_data}
    )

    # Return updated document
    updated_doc = await db["user_plans"].find_one({"_id": obj_id})

    # 4. If doctor-vetted, dynamically index in vector store for RAG
    if updated_doc.get("is_doctor_vetted"):
        try:
            from app.controllers.rag_controller import add_verified_plan_to_vectorstore
            # Backfill metadata if missing (for legacy records)
            full_doc_for_rag = await _backfill_patient_metadata(dict(updated_doc), db)
            await add_verified_plan_to_vectorstore(full_doc_for_rag)
        except Exception as ve:
            logger.error(f"Failed to dynamically index doctor-vetted plan {plan_id} in ChromaDB: {ve}")

    updated_doc["id"] = str(updated_doc["_id"])
    del updated_doc["_id"]


    if isinstance(updated_doc["created_at"], datetime):
        updated_doc["created_at"] = updated_doc["created_at"].isoformat()
    if isinstance(updated_doc.get("reviewed_at"), datetime):
        updated_doc["reviewed_at"] = updated_doc["reviewed_at"].isoformat()

    return updated_doc
