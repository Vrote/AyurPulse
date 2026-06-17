"""
chat_controller.py
-------------------
LLM controller for the Ayurvedic Knowledge Chatbot.

Architecture:
  User message → ChatGroq LLM generates answer
  → answer returned to route handler (with empty sources list)
"""

import os
from functools import lru_cache
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate

from app.config.settings import settings

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


async def handle_chat_message(user_message: str, user_id: str, history: list = None) -> dict:
    """
    Main entry point for processing a user's Ayurvedic question.
    Answers using the LLM directly, with full conversation history for context.
    """
    use_mock = _is_dummy_api_key()

    if use_mock:
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

        # Build message list: system prompt + conversation history + current question
        messages = [SystemMessage(content=GENERAL_SYSTEM_PROMPT)]

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
