"""
Prakriti Assessment Engine — Determining Dosha based on the "Quick 6" Questions.
Designed to minimize user frustration by using only the most discriminative questions.
"""

from typing import Dict, List, Optional

# The "Quick 6" — Simple Question Set
# 0 = Vata, 1 = Pitta, 2 = Kapha
PRAKRITI_MAPPING = {
    "body_frame": ["small_thin", "medium", "large_heavy"],
    "hunger":     ["irregular", "very_strong", "slow"],
    "sleep":      ["light", "sound", "deep"],
    "feeling":    ["cold", "hot", "cool"],
    "digestion":  ["gas_bloat", "burning", "heavy"],
    "mood":       ["quick_anxious", "focused_irritable", "calm"],
}

def calculate_dosha(answers: Dict[str, str]) -> str:
    """Determine dominant Dosha using simple 6-question logic."""
    scores = {"vata": 0, "pitta": 0, "kapha": 0}

    for key, val in answers.items():
        if key not in PRAKRITI_MAPPING:
            continue
        
        mapping = PRAKRITI_MAPPING[key]
        if val == mapping[0]: scores["vata"] += 1
        elif val == mapping[1]: scores["pitta"] += 1
        elif val == mapping[2]: scores["kapha"] += 1

    dominant = max(scores, key=lambda k: scores[k])
    return f"{dominant}_dominant"


def get_all_questions() -> Dict:
    """Unified '1-Form' for the frontend including all 4 assessment sections."""
    return {
        "unified_form": [
            # SECTION 1: DOSHA (PRAKRITI)
            {
                "section": "1. Body Nature",
                "id": "body_frame",
                "label": "How is your body?",
                "type": "select",
                "options": [
                    {"value": "small_thin", "text": "Small / Thin"},
                    {"value": "medium", "text": "Medium"},
                    {"value": "large_heavy", "text": "Large / Heavy"}
                ]
            },
            {
                "section": "1. Body Nature",
                "id": "hunger",
                "label": "How is your hunger?",
                "type": "select",
                "options": [
                    {"value": "irregular", "text": "Irregular (Up & Down)"},
                    {"value": "very_strong", "text": "Very Strong"},
                    {"value": "slow", "text": "Slow (Can skip meals)"}
                ]
            },
            {
                "section": "1. Body Nature",
                "id": "sleep",
                "label": "How do you sleep?",
                "type": "select",
                "options": [
                    {"value": "light", "text": "Light Sleep"},
                    {"value": "sound", "text": "Sound Sleep"},
                    {"value": "deep", "text": "Deep / Long Sleep"}
                ]
            },
            {
                "section": "1. Body Nature",
                "id": "feeling",
                "label": "How do you usually feel?",
                "type": "select",
                "options": [
                    {"value": "cold", "text": "Cold most of the time"},
                    {"value": "hot", "text": "Hot most of the time"},
                    {"value": "cool", "text": "Cool / Clammy"}
                ]
            },
            {
                "section": "1. Body Nature",
                "id": "digestion",
                "label": "How is your digestion?",
                "type": "select",
                "options": [
                    {"value": "gas_bloat", "text": "Gas / Bloating"},
                    {"value": "burning", "text": "Burning / Acidity"},
                    {"value": "heavy", "text": "Heavy after eating"}
                ]
            },
            {
                "section": "1. Body Nature",
                "id": "mood",
                "label": "How is your mood?",
                "type": "select",
                "options": [
                    {"value": "quick_anxious", "text": "Quick / Anxious"},
                    {"value": "focused_irritable", "text": "Focused / Irritable"},
                    {"value": "calm", "text": "Calm / Slow"}
                ]
            },

            # SECTION 2: SKIN PROFILE
            {
                "section": "2. Skin & Age",
                "id": "skin_type",
                "label": "What is your Skin Type?",
                "type": "select",
                "options": [
                    {"value": "oily", "text": "Oily"},
                    {"value": "dry", "text": "Dry"},
                    {"value": "sensitive", "text": "Sensitive"},
                    {"value": "combination", "text": "Combination (Mixed)"},
                    {"value": "normal", "text": "Normal / Balanced"}
                ]
            },
            {
                "section": "2. Skin & Age",
                "id": "age_group",
                "label": "Select your Age Group:",
                "type": "select",
                "options": [
                    {"value": "10-20", "text": "Teen (10 - 20)"},
                    {"value": "21-30", "text": "Young (21 - 30)"},
                    {"value": "31-40", "text": "Adult (31 - 40)"},
                    {"value": "40+", "text": "Senior (40+)"}
                ]
            },

            # SECTION 3: SEASON
            {
                "section": "3. Environment",
                "id": "season",
                "label": "What is the current Season?",
                "type": "select",
                "options": [
                    {"value": "summer", "text": "☀️ Summer"},
                    {"value": "winter", "text": "❄️ Winter"},
                    {"value": "monsoon", "text": "🌧️ Monsoon"},
                    {"value": "autumn", "text": "🍂 Autumn"}
                ]
            },

            # SECTION 4: LIFESTYLE
            {
                "section": "4. Lifestyle",
                "id": "lifestyle",
                "label": "Select everything that applies to you:",
                "type": "multiselect",
                "options": [
                    {"value": "high_stress", "text": "😰 I am under High Stress"},
                    {"value": "poor_sleep", "text": "🥱 I am not sleeping enough"},
                    {"value": "low_water", "text": "🥛 I drink very little water"},
                    {"value": "vegan", "text": "🍱 I am Vegan (no dairy/honey)"},
                    {"value": "female", "text": "👩 I am Female"}
                ]
            }
        ]
    }
