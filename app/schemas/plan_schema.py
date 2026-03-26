from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

# --- INPUT MODELS 

class DoshaAnswers(BaseModel):
    """The Quick 6-Question Assessment Answers (Simple Version)."""
    body_frame: str = Field(..., description="small_thin / medium / large_heavy")
    hunger:     str = Field(..., description="irregular / very_strong / slow")
    sleep:      str = Field(..., description="light / sound / deep")
    feeling:    str = Field(..., description="cold / hot / cool")
    digestion:  str = Field(..., description="gas_bloat / burning / heavy")
    mood:       str = Field(..., description="quick_anxious / focused_irritable / calm")

class PlanRequest(BaseModel):
    """Data required to generate a personalized AyurPulse plan."""
    prediction_id: str = Field(..., description="MongoDB ID from the skin analysis result")
    dosha_answers: DoshaAnswers
    skin_type:     str = Field(..., description="oily / dry / sensitive / combination / normal")
    age_group:     str = Field(..., description="10-20 / 21-30 / 31-40 / 40+")
    season:        str = Field(..., description="summer / winter / monsoon / autumn")
    lifestyle:     List[str] = Field(default=[], description="['high_stress', 'low_water', 'vegan', 'female', 'poor_sleep']")


# --- OUTPUT MODELS ---

class RoutineStep(BaseModel):
    time: str
    routine: List[str]
    ingredients: List[str]
    procedure: List[str] = Field(default=[], description="Step-by-step instructions (e.g., '1. Mix powder with water', '2. Apply on face'...)")

class DietPlan(BaseModel):
    breakfast: str
    lunch: str
    dinner: str
    drinks: List[str]
    avoid: List[str]

class DayPlan(BaseModel):
    day: int
    theme: str
    morning: RoutineStep
    diet: DietPlan
    evening: RoutineStep
    yoga: str
    tip: str

class WeeklySummary(BaseModel):
    key_ingredients: List[str]
    key_diet_changes: List[str]
    expected_results: str
    continue_after_7_days: str

class PlanResponse(BaseModel):
    status: str = "success"
    plan_id: str
    id: Optional[str] = Field(None, description="MongoDB ID of the saved plan")
    title: str
    overview: str
    dosha_focus: str
    is_doctor_vetted: bool = Field(default=False, description="Flag: True if a doctor has reviewed and approved this plan")
    is_doctor_modified: bool = Field(default=False, description="Flag: True if the doctor actually changed the plan content")
    doctor_notes: Optional[str] = Field(None, description="Direct notes from the doctor to the user")
    doctor_name: Optional[str] = Field(None, description="Name of the doctor who reviewed the plan")
    reviewed_at: Optional[str] = Field(None, description="When the doctor last reviewed the plan")
    personalization_notes: List[str] = []
    days: List[DayPlan]
    weekly_summary: WeeklySummary
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class PlanReviewRequest(BaseModel):
    """Data sent by a doctor to approve or modify a plan."""
    is_doctor_vetted: bool = True
    doctor_notes: Optional[str] = None
    modified_plan: Optional[Dict] = None # Full or partial plan object if modifications were made
