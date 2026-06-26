"""
Ingest Ayurvedic Plans into ChromaDB.

One-time script to:
  1. Read ayurvedic_plans_v2.json from app/data/
  2. Convert each of the 15 plans into a LangChain Document
  3. Embed using HuggingFace Inference API (no local model downloads)
  4. Store in ChromaDB at ./chroma_db (persisted to disk)

Usage:
    python -m app.utils.ingest_plans
"""

import json
import os
import sys


def main():
    try:
        from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
        from langchain_chroma import Chroma
        from langchain_core.documents import Document
        from app.config.settings import settings

        # --- 1. Load the plans JSON ---
        json_path = os.path.join("app", "data", "ayurvedic_plans_v2.json")

        if not os.path.exists(json_path):
            print(f"ERROR: Plans file not found at '{json_path}'")
            sys.exit(1)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        plans_data = data.get("plans", {})

        if not plans_data:
            print("ERROR: No plans found in JSON file.")
            sys.exit(1)

        # --- 2. Convert each plan to a LangChain Document ---
        documents = []

        for condition, dosha_variants in plans_data.items():
            for dosha_key, plan in dosha_variants.items():
                # Serialize the full plan as a readable string for page_content
                plan_text = (
                    f"Condition: {condition}\n"
                    f"Dosha: {dosha_key}\n"
                    f"Plan ID: {plan.get('plan_id', 'unknown')}\n"
                    f"Title: {plan.get('title', '')}\n"
                    f"Overview: {plan.get('overview', '')}\n"
                    f"Dosha Focus: {plan.get('dosha_focus', '')}\n\n"
                )

                # Include day-by-day details
                for day_data in plan.get("days", []):
                    plan_text += f"--- Day {day_data.get('day', '?')} ---\n"
                    plan_text += f"Theme: {day_data.get('theme', '')}\n"

                    # Morning
                    morning = day_data.get("morning", {})
                    plan_text += f"Morning ({morning.get('time', '')}):\n"
                    for step in morning.get("routine", []):
                        plan_text += f"  - {step}\n"
                    plan_text += f"  Ingredients: {', '.join(morning.get('ingredients', []))}\n"

                    # Diet
                    diet = day_data.get("diet", {})
                    plan_text += f"Diet:\n"
                    plan_text += f"  Breakfast: {diet.get('breakfast', '')}\n"
                    plan_text += f"  Lunch: {diet.get('lunch', '')}\n"
                    plan_text += f"  Dinner: {diet.get('dinner', '')}\n"
                    plan_text += f"  Drinks: {', '.join(diet.get('drinks', []))}\n"
                    plan_text += f"  Avoid: {', '.join(diet.get('avoid', []))}\n"

                    # Evening
                    evening = day_data.get("evening", {})
                    plan_text += f"Evening ({evening.get('time', '')}):\n"
                    for step in evening.get("routine", []):
                        plan_text += f"  - {step}\n"
                    plan_text += f"  Ingredients: {', '.join(evening.get('ingredients', []))}\n"

                    # Yoga and Tip
                    plan_text += f"Yoga: {day_data.get('yoga', '')}\n"
                    plan_text += f"Tip: {day_data.get('tip', '')}\n\n"

                # Weekly summary
                ws = plan.get("weekly_summary", {})
                plan_text += "Weekly Summary:\n"
                plan_text += f"  Key Ingredients: {', '.join(ws.get('key_ingredients', []))}\n"
                plan_text += f"  Key Diet Changes: {', '.join(ws.get('key_diet_changes', []))}\n"
                plan_text += f"  Expected Results: {ws.get('expected_results', '')}\n"
                plan_text += f"  Continue After 7 Days: {ws.get('continue_after_7_days', '')}\n"

                doc = Document(
                    page_content=plan_text,
                    metadata={
                        "condition": condition,
                        "dosha": dosha_key,
                        "plan_id": plan.get("plan_id", "unknown")
                    }
                )
                documents.append(doc)

        print(f"Prepared {len(documents)} plan documents for ingestion.")

        # --- 3. Initialize embeddings (API-based, no local model) ---
        if not settings.HUGGINGFACE_API_KEY:
            print("ERROR: HUGGINGFACE_API_KEY is not set in .env file.")
            sys.exit(1)

        embeddings = HuggingFaceInferenceAPIEmbeddings(
            api_key=settings.HUGGINGFACE_API_KEY,
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            api_url="https://router.huggingface.co/hf-inference/models/sentence-transformers/all-MiniLM-L6-v2/pipeline/feature-extraction"
        )

        # --- 4. Store in ChromaDB ---
        chroma_path = "./chroma_db"
        print(f"Embedding and storing in ChromaDB at '{chroma_path}'...")

        Chroma.from_documents(
            documents,
            embeddings,
            persist_directory=chroma_path
        )

        print(f"Ingestion complete. {len(documents)} plans stored.")

    except Exception as e:
        print(f"ERROR during ingestion: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
