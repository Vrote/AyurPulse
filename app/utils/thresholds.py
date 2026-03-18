from app.config.settings import settings

# Class names — must match the order used during model training
CLASS_NAMES = ["acne", "blackheads", "dark spots", "pores", "wrinkles"]

# Per-class thresholds
# Wrinkles require higher confidence because the model is stricter for age-related features
THRESHOLDS = {
    "acne":       settings.DISEASE_THRESHOLD,
    "blackheads": settings.DISEASE_THRESHOLD,
    "dark spots": settings.DISEASE_THRESHOLD,
    "pores":      settings.DISEASE_THRESHOLD,
    "wrinkles":   settings.WRINKLE_THRESHOLD,
}


def get_threshold(class_name: str) -> float:
    """Return confidence threshold for a given class name."""
    return THRESHOLDS.get(class_name, settings.DISEASE_THRESHOLD)