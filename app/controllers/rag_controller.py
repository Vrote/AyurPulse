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

        # --- Step 3: Retrieve top similar plan with metadata filter ---
        try:
            search_kwargs = {
                "k": 1,
                "filter": {
                    "$and": [
                        {"condition": condition},
                        {"dosha": dominant_dosha}
                    ]
                }
            }
            retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
            retrieved_docs = retriever.invoke(query)
        except Exception as e:
            logger.error(f"ChromaDB retrieval failed: {e}")
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
