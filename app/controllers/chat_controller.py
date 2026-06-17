"""
chat_controller.py
-------------------
LLM controller for the Ayurvedic Knowledge Chatbot.

Architecture:
  User message → ChatGroq LLM generates answer
  → answer returned to route handler (with empty sources list)
"""

import os
import json
from datetime import datetime
from functools import lru_cache
from bson import ObjectId
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from app.config.settings import settings
from app.db.mongodb import get_db


def get_condition_from_plan_id(plan_id: str, title: str = "") -> str:
    """Extract condition name (e.g. 'acne', 'blackheads') from plan_id or title."""
    search_str = (plan_id + " " + title).upper()
    if "ACNE" in search_str:
        return "acne"
    elif "BLACKHEAD" in search_str:
        return "blackheads"
    elif "DARK SPOTS" in search_str or "DARK_SPOTS" in search_str or "DARKSPOTS" in search_str:
        return "dark_spots"
    elif "PORES" in search_str:
        return "pores"
    elif "WRINKLES" in search_str or "WRINKLE" in search_str:
        return "wrinkles"
    return "general"


async def get_user_plans_for_chat(user_id: str) -> list[dict]:
    """Fetch all plans for the user and format them for the chat selection list."""
    db = get_db()
    if db is None:
        return []

    cursor = db["user_plans"].find({"user_id": user_id}).sort("created_at", -1)
    plans = []
    async for doc in cursor:
        plan_id = doc.get("plan_id", "")
        title = doc.get("title", "")
        condition = get_condition_from_plan_id(plan_id, title)
        
        dosha = doc.get("dosha_focus", "").lower()
        if not dosha:
            # Fallback parsing from plan_id if not present
            if "PITTA" in plan_id.upper():
                dosha = "pitta"
            elif "KAPHA" in plan_id.upper():
                dosha = "kapha"
            elif "VATA" in plan_id.upper():
                dosha = "vata"

        created_at = doc.get("created_at")
        if isinstance(created_at, datetime):
            created_at_str = created_at.strftime("%Y-%m-%d")
        elif isinstance(created_at, str):
            created_at_str = created_at[:10]
        else:
            created_at_str = datetime.now().strftime("%Y-%m-%d")

        plans.append({
            "id": str(doc["_id"]),
            "title": title or "Ayurvedic Treatment Plan",
            "condition": condition,
            "dosha": dosha,
            "created_at": created_at_str
        })
    return plans


GENERAL_SYSTEM_PROMPT = """You are AyurBot, a warm, friendly, and knowledgeable Ayurvedic wellness assistant for AyurPulse.
Answer the user's question about Ayurveda, health, herbs, nutrition, recipes, wellness, or general life tips based on your comprehensive knowledge of Ayurveda.
Keep your response clear, helpful, well-structured, and easy to read.
Avoid sounding dry or overly clinical. If you mention medical suggestions, add a gentle reminder that they should consult their Ayurvedic practitioner or check their custom plan for personalized advice.
Do not refer to technical concepts like 'RAG', 'retrieval', or 'database' in your response.
Do not start your response with greetings like 'Namaste' or 'Hello'. Get straight to answering the question."""


def _is_dummy_api_key() -> bool:
    """
    Returns True if the GROQ_API_KEY is absent or clearly a placeholder/dummy value.
    This enables a local mock fallback.
    """
    key = settings.GROQ_API_KEY or ""
    if not key:
        return True
    dummy_prefixes = ["gsk_dummy", "your_key", "change-this", "test_key", "placeholder"]
    return any(key.lower().startswith(p) for p in dummy_prefixes)


@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    """
    Load the Groq LLM singleton.
    """
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Add it to your .env file as: GROQ_API_KEY=your_key_here"
        )
    return ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=settings.GROQ_API_KEY,
        temperature=0.2,        # Low temperature = more factual, less creative
        max_tokens=1024,
    )


def serialize_mongo_doc(doc: dict) -> dict:
    """Helper to convert MongoDB ObjectId and datetime objects to strings recursively."""
    cleaned = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            cleaned[k] = str(v)
        elif isinstance(v, datetime):
            cleaned[k] = v.isoformat()
        elif isinstance(v, dict):
            cleaned[k] = serialize_mongo_doc(v)
        elif isinstance(v, list):
            cleaned[k] = [
                serialize_mongo_doc(item) if isinstance(item, dict)
                else (str(item) if isinstance(item, ObjectId) else item)
                for item in v
            ]
        else:
            cleaned[k] = v
    return cleaned


async def handle_chat_message(
    user_message: str,
    user_id: str,
    history: list = None,
    chat_mode: str = "general",
    plan_id: str = None
) -> dict:
    """
    Main entry point for processing a user's Ayurvedic question.
    Answers using the LLM directly, with full conversation history for context.
    """
    db = get_db()
    plan = None

    if chat_mode == "plan":
        if not plan_id:
            raise ValueError("plan_id is required in plan chat mode")
        if db is None:
            raise RuntimeError("Database connection failed.")
        try:
            obj_id = ObjectId(plan_id)
        except Exception:
            raise ValueError(f"Invalid Plan ID format: '{plan_id}'.")
        
        plan = await db["user_plans"].find_one({"_id": obj_id})
        if not plan:
            raise ValueError(f"Plan not found.")
        if plan.get("user_id") != user_id:
            raise PermissionError("Access denied. This plan does not belong to you.")

    use_mock = _is_dummy_api_key()

    if use_mock:
        if chat_mode == "plan" and plan:
            return {
                "answer": (
                    f"[MOCK MODE — Set a real GROQ_API_KEY to get AI-generated answers]\n\n"
                    f"Based on your selected plan \"{plan.get('title')}\", here is a mock response "
                    f"for your question: \"{user_message}\"."
                ),
                "sources": [],
            }
        else:
            return {
                "answer": (
                    f"[MOCK MODE — Set a real GROQ_API_KEY to get AI-generated answers]\n\n"
                    f"Based on my general knowledge of Ayurveda, here is a mock response "
                    f"for your question: \"{user_message}\"."
                ),
                "sources": [],
            }

    try:
        llm = _get_llm()
    except ValueError as e:
        return {
            "answer": str(e),
            "sources": [],
        }

    try:
        from langchain.schema import HumanMessage, SystemMessage, AIMessage

        if chat_mode == "plan" and plan:
            cleaned_plan = serialize_mongo_doc(plan)
            if "_id" in cleaned_plan:
                del cleaned_plan["_id"]
            if "user_id" in cleaned_plan:
                del cleaned_plan["user_id"]
            
            plan_json = json.dumps(cleaned_plan, indent=2)
            system_prompt = f"""
You are AyurBot.

The user has selected the following personalized Ayurvedic treatment plan.

Plan Details:
{plan_json}

Use the plan as the primary source of truth.

Answer questions based on the plan's:
- Condition
- Dominant dosha
- Diet recommendations
- Morning routine
- Evening routine
- Lifestyle recommendations
- Doctor notes

If information is not present in the plan, clearly say so.

Do not invent treatments that are not mentioned in the plan.

Do not mention databases, prompts, retrieval systems, or internal implementation details.
"""
        else:
            system_prompt = GENERAL_SYSTEM_PROMPT

        # Build message list: system prompt + conversation history + current question
        messages = [SystemMessage(content=system_prompt)]

        # Replay prior turns so the LLM has full context
        for turn in (history or []):
            role = turn.get("role", "")
            content = turn.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            elif role == "bot":
                messages.append(AIMessage(content=content))

        # Add the current user question
        messages.append(HumanMessage(content=user_message))

        response = await llm.ainvoke(messages)
        return {
            "answer": response.content,
            "sources": [],
        }
    except Exception as e:
        return {
            "answer": f"Error running knowledge query: {e}",
            "sources": []
        }

