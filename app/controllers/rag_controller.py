"""
RAG Controller — Retrieval-Augmented Generation for Personalized Ayurvedic Plans.

Flow:
  1. Build a query from user's condition, dosha, age, and lifestyle data
  2. Retrieve top-3 similar plans from ChromaDB (vector similarity)
  3. Send retrieved plans + user context to Groq LLM (llama-3.1-8b-instant)
  4. Parse and validate the LLM's JSON response
  5. Return the personalized plan dict, or None on any failure

Design Decisions:
  - ChromaDB vectorstore is lazy-loaded on first request (not at import time)
  - HuggingFaceInferenceAPIEmbeddings used to avoid local model downloads (4GB RAM)
  - Every external call is wrapped in its own try/except — failures never propagate
  - Returns None on failure so the caller falls back to rule-based plan generation
"""

import json
import os
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

# Lazy-load pattern: vectorstore initialized on first request
_vectorstore = None


def get_vectorstore():
    """
    Lazily load the ChromaDB vectorstore from disk.
    Returns None if chroma_db directory doesn't exist or loading fails.
    """
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    chroma_path = "./chroma_db"
    if not os.path.exists(chroma_path):
        logger.warning("ChromaDB directory './chroma_db' does not exist. Run ingest_plans.py first.")
        return None

    try:
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
        from langchain_chroma import Chroma

        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=settings.HUGGINGFACE_API_KEY,
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            api_url="https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
        )

        _vectorstore = Chroma(
            persist_directory=chroma_path,
            embedding_function=embeddings
        )
        logger.info("ChromaDB vectorstore loaded successfully.")
        return _vectorstore

    except Exception as e:
        logger.error(f"Failed to load ChromaDB vectorstore: {e}")
        return None


async def generate_rag_plan(
    condition: str,
    dominant_dosha: str,
    age: str,
    lifestyle_data: dict
) -> dict | None:
    """
    Generate a personalized Ayurvedic plan using RAG (Retrieval-Augmented Generation).

    Args:
        condition: Detected skin condition (e.g., "acne", "dark_spots")
        dominant_dosha: User's dominant dosha (e.g., "pitta_dominant")
        age: User's age group (e.g., "21-30")
        lifestyle_data: Dict with keys like sleep_hours, stress_level, etc.

    Returns:
        A dict matching the plan JSON structure, or None if any step fails.
    """
    try:
        # --- Step 1: Get vectorstore ---
        vectorstore = get_vectorstore()
        if vectorstore is None:
            logger.warning("ChromaDB not available, falling back to rule-based")
            return None

        # --- Step 2: Build retrieval query ---
        query = (
            f"Condition: {condition}, "
            f"Dosha: {dominant_dosha}, "
            f"Age: {age}, "
            f"Sleep: {lifestyle_data.get('sleep_hours', 'unknown')}, "
            f"Stress: {lifestyle_data.get('stress_level', 'unknown')}, "
            f"Water: {lifestyle_data.get('water_intake', 'unknown')}, "
            f"Exercise: {lifestyle_data.get('exercise_frequency', 'unknown')}"
        )

        # --- Step 3: Retrieve top similar plan with metadata filter (tiered: doctor_verified first, fallback to base_template) ---
        retrieved_docs = []
        try:
            # Try finding doctor-verified plan first
            results = vectorstore.similarity_search_with_score(
                query,
                k=1,
                filter={
                    "$and": [
                        {"condition": condition},
                        {"dosha": dominant_dosha},
                        {"plan_type": "doctor_verified"}
                    ]
                }
            )
            if results:
                doc, score = results[0]
                # Chroma distance metric (L2). Lower is closer/better.
                # Threshold of 1.0 represents a close match for dynamic templates (L2 distance < 1.0 corresponds to cosine similarity > 0.5).
                logger.info(f"Doctor-verified plan found. Distance score: {score:.4f}")
                if score < 1.0:
                    retrieved_docs = [doc]
                    logger.info("Using doctor-verified plan as reference context")
                else:
                    logger.info("Doctor-verified plan distance score too high (>= 1.0). Falling back to base template.")
        except Exception as e:
            logger.error(f"Doctor-verified similarity search failed: {e}")

        # If no doctor-verified plan was retrieved or matched threshold, fallback to base template
        if not retrieved_docs:
            try:
                retrieved_docs = vectorstore.similarity_search(
                    query,
                    k=1,
                    filter={
                        "$and": [
                            {"condition": condition},
                            {"dosha": dominant_dosha},
                            {"plan_type": "base_template"}
                        ]
                    }
                )
                if retrieved_docs:
                    logger.info("Using standard base template plan as reference context")
                else:
                    # In case of older/un-migrated database, run fallback query without plan_type
                    retrieved_docs = vectorstore.similarity_search(
                        query,
                        k=1,
                        filter={
                            "$and": [
                                {"condition": condition},
                                {"dosha": dominant_dosha}
                            ]
                        }
                    )
                    if retrieved_docs:
                        logger.info("Using unfiltered fallback template as reference context")
            except Exception as e:
                logger.error(f"Base template ChromaDB retrieval failed: {e}")
                return None

        if not retrieved_docs:
            logger.warning(f"No documents retrieved from ChromaDB for condition={condition}, dosha={dominant_dosha}")
            return None

        # Join retrieved plan texts
        retrieved_plans_text = "\n\n--- RETRIEVED PLAN ---\n\n".join(
            [doc.page_content for doc in retrieved_docs]
        )

        # --- Step 4: Build LLM prompt ---
        # Gemini 1.5 Flash supports up to 8192 output tokens — enough for all 7 days.
        system_message = (
            "You are an expert Ayurvedic wellness planner for AyurPulse. "
            "Generate a personalized plan using the retrieved examples as templates. "
            "Return ONLY a valid raw JSON object. "
            "No explanation. No markdown. No code blocks. No backticks. "
            "Just the raw JSON object starting with { and ending with }."
        )

        user_message = f"""Generate a personalized 7-day Ayurvedic plan for this user:

CONDITION: {condition}
DOSHA: {dominant_dosha}
AGE GROUP: {age}
LIFESTYLE DATA: {json.dumps(lifestyle_data)}

Reference plan from our knowledge base:
{retrieved_plans_text}

REQUIRED OUTPUT FORMAT — return exactly this JSON with all 7 days:
{{
  "plan_id": "<CONDITION>_<DOSHA>_RAG",
  "title": "7-Day Personalized <Dosha> <Condition> Plan",
  "overview": "<2-sentence personalized overview>",
  "dosha_focus": "<dosha without _dominant suffix>",
  "days": [
    {{
      "day": 1,
      "theme": "<theme>",
      "morning": {{"time": "6:00 AM", "routine": ["<step1>", "<step2>"], "ingredients": ["<i1>", "<i2>"], "procedure": ["<p1>", "<p2>"]}},
      "diet": {{"breakfast": "<meal>", "lunch": "<meal>", "dinner": "<meal>", "drinks": ["<drink>"], "avoid": ["<item>"]}},
      "evening": {{"time": "7:00 PM", "routine": ["<step1>"], "ingredients": ["<i1>"], "procedure": ["<p1>"]}},
      "yoga": "<yoga>",
      "tip": "<tip>"
    }}
    ... repeat for days 2 through 7 with unique themes and content ...
  ],
  "weekly_summary": {{
    "key_ingredients": ["<i1>", "<i2>", "<i3>"],
    "key_diet_changes": ["<change1>", "<change2>"],
    "expected_results": "<2 sentences>",
    "continue_after_7_days": "<1 sentence advice>"
  }}
}}

Personalize each day based on lifestyle data. Use authentic Ayurvedic ingredients. Return ONLY the raw JSON."""

        # --- Step 5: Initialize and call Groq LLaMA 3.3 70B ---
        # llama-3.3-70b-versatile is highly capable and has higher TPM limit (12k).
        try:
            from langchain_groq import ChatGroq
            llm = ChatGroq(
                model="llama-3.3-70b-versatile",
                groq_api_key=settings.GROQ_API_KEY,
                max_tokens=4096,
                temperature=0.2
            )
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")
            return None

        try:
            from langchain_core.messages import SystemMessage, HumanMessage
            prompt = [
                SystemMessage(content=system_message),
                HumanMessage(content=user_message)
            ]
            response = llm.invoke(prompt)
        except Exception as e:
            logger.error(f"Groq LLM invocation failed: {e}")
            return None

        # --- Step 6: Parse LLM response ---
        raw = response.content.strip()

        # Defensive: strip markdown code blocks if LLM disobeys prompt instructions
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        try:
            plan = json.loads(raw)
        except json.JSONDecodeError as e:
            logger.error(f"LLM returned invalid JSON: {e}, raw: {raw[:500]}")
            return None

        # --- Step 7: Validate required top-level keys ---
        required_keys = ["plan_id", "title", "overview", "dosha_focus", "days", "weekly_summary"]
        missing_keys = [k for k in required_keys if k not in plan]
        if missing_keys:
            logger.warning(f"RAG plan missing required keys: {missing_keys}")
            return None

        # Validate days array (RAG returns 3 days; rule-based fallback pads to 7)
        if not isinstance(plan.get("days"), list) or len(plan["days"]) == 0:
            logger.warning("RAG plan has empty or invalid 'days' array")
            return None

        # Validate weekly_summary structure
        ws = plan.get("weekly_summary", {})
        ws_required = ["key_ingredients", "key_diet_changes", "expected_results", "continue_after_7_days"]
        missing_ws = [k for k in ws_required if k not in ws]
        if missing_ws:
            logger.warning(f"RAG plan weekly_summary missing keys: {missing_ws}")
            return None

        logger.info(f"RAG plan generated successfully: {plan.get('plan_id', 'unknown')}")
        return plan

    except Exception as e:
        logger.error(f"Unexpected RAG error: {e}")
        return None


async def add_verified_plan_to_vectorstore(plan_data: dict) -> bool:
    """
    Dynamically embed and add a doctor-verified plan to the ChromaDB vector store.
    Uses the unique plan ID to upsert so duplicates are handled cleanly.
    """
    try:
        vectorstore = get_vectorstore()
        if vectorstore is None:
            logger.error("Failed to load vectorstore for adding doctor-verified plan.")
            return False

        # Extract metadata
        plan_id = plan_data.get("id") or str(plan_data.get("_id", "unknown"))
        if plan_id == "unknown":
            logger.error("Cannot add plan to vectorstore: no valid ID found.")
            return False

        # Extract condition from plan_id or metadata
        metadata = plan_data.get("patient_metadata", {})
        condition = "acne"
        plan_id_str = plan_data.get("plan_id", "").upper()
        if "ACNE" in plan_id_str:
            condition = "acne"
        elif "BLACKHEAD" in plan_id_str:
            condition = "blackheads"
        elif "DARK_SPOTS" in plan_id_str or "DARKSPOTS" in plan_id_str or "DARK SPOTS" in plan_id_str:
            condition = "dark_spots"
        elif "PORES" in plan_id_str:
            condition = "pores"
        elif "WRINKLES" in plan_id_str:
            condition = "wrinkles"

        # Dosha focus normalization
        dosha = plan_data.get("dosha_focus", "").lower()
        if not dosha.endswith("_dominant"):
            dosha = f"{dosha}_dominant"

        # Format text representation for vector indexing
        plan_text = (
            f"Plan Type: Doctor-Verified Plan\n"
            f"Condition: {condition}\n"
            f"Dosha: {dosha}\n"
            f"Plan ID: {plan_data.get('plan_id', 'unknown')}\n"
            f"Title: {plan_data.get('title', '')}\n"
            f"Overview: {plan_data.get('overview', '')}\n"
            f"Doctor Notes: {plan_data.get('doctor_notes') or ''}\n"
            f"Doctor Name: {plan_data.get('doctor_name', 'Unknown Doctor')}\n"
            f"Patient Age Group: {metadata.get('age_group', 'unknown')}\n"
            f"Patient Skin Type: {metadata.get('skin_type', 'unknown')}\n"
            f"Patient Lifestyle: {', '.join(metadata.get('lifestyle', []))}\n\n"
        )

        for day in plan_data.get("days", []):
            plan_text += f"--- Day {day.get('day', '?')} ---\n"
            plan_text += f"Theme: {day.get('theme', '')}\n"
            
            # Morning
            morning = day.get("morning", {})
            plan_text += f"Morning ({morning.get('time', '')}):\n"
            for step in morning.get("routine", []):
                plan_text += f"  - {step}\n"
            plan_text += f"  Ingredients: {', '.join(morning.get('ingredients', []))}\n"

            # Diet
            diet = day.get("diet", {})
            plan_text += f"Diet:\n"
            plan_text += f"  Breakfast: {diet.get('breakfast', '')}\n"
            plan_text += f"  Lunch: {diet.get('lunch', '')}\n"
            plan_text += f"  Dinner: {diet.get('dinner', '')}\n"
            plan_text += f"  Drinks: {', '.join(diet.get('drinks', []))}\n"
            plan_text += f"  Avoid: {', '.join(diet.get('avoid', []))}\n"

            # Evening
            evening = day.get("evening", {})
            plan_text += f"Evening ({evening.get('time', '')}):\n"
            for step in evening.get("routine", []):
                plan_text += f"  - {step}\n"
            plan_text += f"  Ingredients: {', '.join(evening.get('ingredients', []))}\n"

            plan_text += f"Yoga: {day.get('yoga', '')}\n"
            plan_text += f"Tip: {day.get('tip', '')}\n\n"

        # Weekly summary
        ws = plan_data.get("weekly_summary", {})
        plan_text += "Weekly Summary:\n"
        plan_text += f"  Key Ingredients: {', '.join(ws.get('key_ingredients', []))}\n"
        plan_text += f"  Key Diet Changes: {', '.join(ws.get('key_diet_changes', []))}\n"
        plan_text += f"  Expected Results: {ws.get('expected_results', '')}\n"
        plan_text += f"  Continue After 7 Days: {ws.get('continue_after_7_days', '')}\n"

        # Add to ChromaDB
        from langchain_core.documents import Document
        doc = Document(
            page_content=plan_text,
            metadata={
                "plan_type": "doctor_verified",
                "condition": condition,
                "dosha": dosha,
                "plan_id": plan_data.get("plan_id", "unknown"),
                "age_group": metadata.get("age_group", "unknown"),
                "skin_type": metadata.get("skin_type", "unknown")
            }
        )

        vectorstore.add_documents([doc], ids=[plan_id])
        logger.info(f"Doctor-verified plan '{plan_id}' successfully added/updated in vectorstore.")
        return True

    except Exception as e:
        logger.error(f"Failed to add doctor-verified plan to vectorstore: {e}")
        return False
