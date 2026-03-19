from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum


class SkinType(str, Enum):
    oily        = "oily"
    dry         = "dry"
    combination = "combination"
    sensitive   = "sensitive"
    normal      = "normal"

class AgeGroup(str, Enum):
    teen   = "10-20"
    young  = "21-30"
    adult  = "31-40"
    mature = "40+"

class Season(str, Enum):
    summer  = "summer"
    winter  = "winter"
    monsoon = "monsoon"
    autumn  = "autumn"

class StressLevel(str, Enum):
    low    = "low"
    medium = "medium"
    high   = "high"

class SleepHours(str, Enum):
    poor    = "less than 6"
    average = "6-8"
    good    = "more than 8"

class WaterIntake(str, Enum):
    low    = "less than 4 glasses"
    medium = "4-8 glasses"
    high   = "more than 8 glasses"

class Gender(str, Enum):
    male   = "male"
    female = "female"
    other  = "other"

class DietType(str, Enum):
    vegetarian     = "vegetarian"
    non_vegetarian = "non-vegetarian"
    vegan          = "vegan"


# ── Request ────────────────────────────────────────────────────────────────────

class SkinProfileRequest(BaseModel):
    """
    8-field form. System automatically uses your latest skin analysis result.
    No need to pass condition — backend fetches it from your prediction history.
    """
    # Fallback — only for testing via Swagger
    # In real app this is never needed — system auto-fetches latest prediction
    detected_condition: Optional[str] = Field(
        None,
        example=None,
        description="Leave empty. System auto-uses your latest skin analysis result."
    )

    # 8 profile fields — always required
    skin_type:    SkinType    = Field(..., example="oily")
    age_group:    AgeGroup    = Field(..., example="21-30")
    season:       Season      = Field(..., example="summer")
    stress_level: StressLevel = Field(..., example="medium")
    sleep_hours:  SleepHours  = Field(..., example="6-8")
    water_intake: WaterIntake = Field(..., example="4-8 glasses")
    gender:       Gender      = Field(..., example="female")
    diet_type:    DietType    = Field(..., example="vegetarian")

    @field_validator("detected_condition")
    @classmethod
    def validate_condition(cls, v: str) -> str:
        if v is None:
            return v
        valid = ["acne", "blackheads", "dark spots", "pores", "wrinkles"]
        v = v.lower().strip()
        if v not in valid:
            raise ValueError(f"Must be one of: {', '.join(valid)}")
        return v


# ── Checklist item ─────────────────────────────────────────────────────────────

class ChecklistItem(BaseModel):
    id:       str    # unique e.g. "d1_morning_0"
    category: str    # morning / evening / diet / yoga
    task:     str    # what user reads
    done:     bool = False


# ── Day plan ───────────────────────────────────────────────────────────────────

class DayPlan(BaseModel):
    day:       int
    theme:     str
    checklist: List[ChecklistItem]
    tip:       str


# ── Plan response ──────────────────────────────────────────────────────────────

class PlanResponse(BaseModel):
    status:           str = "success"
    plan_id:          str
    condition:        str
    dosha:            str
    dosha_tip:        str
    plan_title:       str
    key_ingredients:  List[str]
    days:             List[DayPlan]
    weekly_summary:   str
    expected_results: str
    disclaimer:       str


# ── Check-in request / response ────────────────────────────────────────────────

class CheckinRequest(BaseModel):
    plan_id:       str
    day:           int  = Field(..., ge=1, le=7)
    completed_ids: List[str]
    skin_rating:   int  = Field(..., ge=1, le=10,
        description="How does your skin feel today? 1=very bad 10=very good")


class CheckinResponse(BaseModel):
    status:          str = "success"
    day:             int
    completed_count: int
    total_count:     int
    completion_pct:  int
    skin_rating:     int
    message:         str


# ── Progress ───────────────────────────────────────────────────────────────────

class DayProgress(BaseModel):
    day:             int
    completed_count: int
    total_count:     int
    completion_pct:  int
    skin_rating:     Optional[int]  = None
    checked_in:      bool


class ProgressResponse(BaseModel):
    status:          str = "success"
    plan_id:         str
    condition:       str
    overall_pct:     int
    days_checked_in: int
    days:            List[DayProgress]
    avg_skin_rating: Optional[float] = None
    message:         str