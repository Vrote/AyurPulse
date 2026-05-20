import torch
import torch.nn.functional as F
import uuid
import os
from datetime import datetime, timezone

from app.models.prediction_model import load_model
from app.utils.image_preprocess import preprocess_image, validate_image_size
from app.utils.thresholds import CLASS_NAMES, get_threshold
from app.schemas.prediction_schema import PredictionResponse, ClassProbability
from app.config.settings import settings
from app.db.mongodb import get_db


async def predict_skin_condition(
    image_bytes: bytes,
    filename:    str,
    user_id:     str = None,
) -> PredictionResponse:
    """
    Preprocess image → run model → apply thresholds → save to MongoDB → return result.

    Saves to skin_predictions collection:
    {
        user_id, filename, detected_conditions,
        all_probabilities, consult_doctor, created_at
    }

    Returns prediction_id so frontend can pass it directly to /plan/generate.
    User never has to type their skin condition manually.
    """

    # 1. Validate file size
    validate_image_size(len(image_bytes), max_mb=settings.MAX_FILE_SIZE_MB)

    # 2. Save image to uploads/
    os.makedirs(settings.UPLOAD_FOLDER, exist_ok=True)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    save_path       = os.path.join(settings.UPLOAD_FOLDER, unique_filename)
    with open(save_path, "wb") as f:
        f.write(image_bytes)

    # 3. Preprocess → tensor
    tensor = preprocess_image(image_bytes)

    # 4. Model inference
    model, device = load_model()
    tensor        = tensor.to(device)

    with torch.no_grad():
        outputs = model(tensor)
        probs   = F.softmax(outputs, dim=1)

    prob_values = probs[0].cpu().numpy() * 100

    # 5. Build probabilities list
    all_probabilities = [
        ClassProbability(class_name=cls, confidence=round(float(prob), 2))
        for cls, prob in zip(CLASS_NAMES, prob_values)
    ]

    # 6. Apply thresholds
    detected_conditions = [
        cls for cls, prob in zip(CLASS_NAMES, prob_values)
        if prob >= get_threshold(cls)
    ]

    # 7. Message and next step
    if detected_conditions:
        condition_list = ", ".join(detected_conditions)
        message        = f"Detected: {condition_list}."
        consult_doctor = False
        next_step      = (
            "Use the prediction_id from this response to generate "
            "your personalized Ayurvedic plan at POST /api/v1/plan/generate"
        )
    else:
        message        = (
            "No condition detected with high confidence. "
            "Consult a dermatologist if you notice a skin problem."
        )
        consult_doctor = True
        next_step      = "Please consult a dermatologist for further evaluation."

    # 8. Save to MongoDB skin_predictions collection
    prediction_id = None
    db = get_db()
    if db is not None:
        doc = {
            "user_id":             user_id,
            "filename":            unique_filename,
            "detected_conditions": detected_conditions,
            "all_probabilities": [
                {"class_name": p.class_name, "confidence": p.confidence}
                for p in all_probabilities
            ],
            "consult_doctor": consult_doctor,
            "message":        message,
            "created_at":     datetime.now(timezone.utc),
        }
        result        = await db["skin_predictions"].insert_one(doc)
        prediction_id = str(result.inserted_id)

    return PredictionResponse(
        status              = "success",
        prediction_id       = prediction_id,
        detected_conditions = detected_conditions,
        all_probabilities   = all_probabilities,
        message             = message,
        consult_doctor      = consult_doctor,
        next_step           = next_step,
    )