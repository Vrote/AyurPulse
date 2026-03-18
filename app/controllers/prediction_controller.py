import torch
import torch.nn.functional as F
import uuid
import os
from datetime import datetime

from app.models.prediction_model import load_model
from app.utils.image_preprocess import preprocess_image, validate_image_size
from app.utils.thresholds import CLASS_NAMES, get_threshold
from app.schemas.prediction_schema import PredictionResponse, ClassProbability
from app.config.settings import settings


async def predict_skin_condition(image_bytes: bytes, filename: str) -> PredictionResponse:
    """
    Core business logic: preprocess image → run model → apply thresholds → return result.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        filename:    Original filename (used to save to uploads/).

    Returns:
        PredictionResponse with detected conditions and confidence scores.
    """

    # 1. Validate file size
    validate_image_size(len(image_bytes), max_mb=settings.MAX_FILE_SIZE_MB)

    # 2. Save image to uploads/ folder (frontend can reference this later)
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    save_path = os.path.join(settings.UPLOAD_FOLDER, unique_filename)
    with open(save_path, "wb") as f:
        f.write(image_bytes)

    # 3. Preprocess image into tensor
    tensor = preprocess_image(image_bytes)

    # 4. Load model and run inference
    model, device = load_model()
    tensor = tensor.to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs = F.softmax(outputs, dim=1)

    # 5. Convert probabilities to percentage list
    prob_values = probs[0].cpu().numpy() * 100  # shape: (5,)

    # 6. Build all_probabilities list for frontend (charts etc.)
    all_probabilities = [
        ClassProbability(class_name=cls, confidence=round(float(prob), 2))
        for cls, prob in zip(CLASS_NAMES, prob_values)
    ]

    # 7. Apply per-class thresholds to find detected conditions
    detected_conditions = []
    for cls, prob in zip(CLASS_NAMES, prob_values):
        threshold = get_threshold(cls)
        if prob >= threshold:
            detected_conditions.append(cls)

    # 8. Build human-readable message
    if detected_conditions:
        condition_list = ", ".join(detected_conditions)
        message = f"Possible skin condition(s) detected: {condition_list}."
        consult_doctor = False
    else:
        message = (
            "No condition from the 5 known classes was detected with high confidence. "
            "If you still notice a skin problem, please consult a dermatologist."
        )
        consult_doctor = True

    return PredictionResponse(
        status="success",
        detected_conditions=detected_conditions,
        all_probabilities=all_probabilities,
        message=message,
        consult_doctor=consult_doctor,
    )