from pydantic import BaseModel
from typing import List, Optional


class ClassProbability(BaseModel):
    class_name: str
    confidence: float


class PredictionResponse(BaseModel):
    status:              str
    prediction_id:       Optional[str] = None  # MongoDB _id — pass to /plan/generate
    detected_conditions: List[str]
    all_probabilities:   List[ClassProbability]
    message:             str
    consult_doctor:      bool
    next_step:           Optional[str] = None  # tells frontend what to do next


class ErrorResponse(BaseModel):
    status:  str = "error"
    message: str
    detail:  Optional[str] = None