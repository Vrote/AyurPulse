# app/controllers/prediction_controller.py
import os
import uuid
import torch
import torch.nn.functional as F
from fastapi import UploadFile, HTTPException, BackgroundTasks

from app.models.prediction_model import load_model
from app.utils.image_preprocess import preprocess_image
from app.utils.thresholds import class_names, disease_threshold, wrinkle_threshold

# Load model once at startup
try:
    model = load_model()
    model.eval()
except Exception as e:
    raise RuntimeError(f"Failed to load model: {e}")


def remove_file_later(file_path: str, background_tasks: BackgroundTasks):
    """Schedule a file to be deleted after processing."""
    background_tasks.add_task(lambda: os.remove(file_path) if os.path.exists(file_path) else None)


async def predict_skin(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Predict skin diseases from an uploaded image file.
    Returns detected classes and confidence scores.
    """
    # Validate file type
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Invalid image format. Only JPG, JPEG, PNG allowed.")

    # Save file with unique name
    try:
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        upload_path = os.path.join("uploads", unique_filename)

        with open(upload_path, "wb") as buffer:
            buffer.write(await file.read())

        # Schedule deletion after prediction
        remove_file_later(upload_path, background_tasks)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {e}")

    # Preprocess image and predict
    try:
        image_tensor = preprocess_image(upload_path)

        with torch.no_grad():
            outputs = model(image_tensor)
            probs = F.softmax(outputs, dim=1)[0].cpu().numpy() * 100

        detected = []
        confidence = {}

        for i, cls in enumerate(class_names):
            confidence[cls] = round(float(probs[i]), 2)
            if cls == "wrinkles" and probs[i] >= wrinkle_threshold:
                detected.append(cls)
            elif cls != "wrinkles" and probs[i] >= disease_threshold:
                detected.append(cls)

        return {
            "detected_classes": detected,
            "confidence_scores": confidence
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")