from pydantic import BaseModel
from typing import List, Optional


class ClassProbability(BaseModel):
    """Confidence score for a single skin condition class."""
    class_name: str
    confidence: float   # percentage, e.g. 92.45


class PredictionResponse(BaseModel):
    """
    Full API response returned after skin analysis.

    Fields:
        status:           "success" or "error"
        detected_conditions: List of conditions that crossed their threshold.
        all_probabilities:   Raw confidence for all 5 classes (useful for frontend charts).
        message:          Human-readable summary.
        consult_doctor:   True when no condition is detected or confidence is borderline.
    """
    status: str
    detected_conditions: List[str]
    all_probabilities: List[ClassProbability]
    message: str
    consult_doctor: bool


class ErrorResponse(BaseModel):
    """Returned when something goes wrong."""
    status: str = "error"
    message: str
    detail: Optional[str] = None