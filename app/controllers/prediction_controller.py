import os
import uuid
import torch
import torch.nn.functional as F
from fastapi import UploadFile, HTTPException, BackgroundTasks

from app.models.prediction_model import load_model
from app.utils.image_preprocess import preprocess_image
from app.utils.thresholds import class_names, disease_threshold, wrinkle_threshold


# Lazy load model (best practice)
model = None


def get_model():
    global model
    if model is None:
        try:
            model = load_model()
            model.eval()
        except Exception as e:
            raise RuntimeError(f"Model loading failed: {e}")
    return model


def delete_file(file_path: str):
    """Safely delete file."""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception:
        pass


async def predict_skin(file: UploadFile, background_tasks: BackgroundTasks):
    """
    Predict skin diseases from uploaded image.
    """

    # Validate file type
    if not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Only JPG, JPEG, PNG allowed."
        )

    # Ensure uploads folder exists
    os.makedirs("uploads", exist_ok=True)

    try:
        # Generate unique filename
        ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{ext}"
        upload_path = os.path.join("uploads", unique_filename)

        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        # Schedule file deletion after response
        background_tasks.add_task(delete_file, upload_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"File upload failed: {str(e)}"
        )

    try:
        # Preprocess image
        image_tensor = preprocess_image(upload_path)

        # Get model
        model = get_model()

        # Prediction
        with torch.no_grad():
            outputs = model(image_tensor)
            probs = F.softmax(outputs, dim=1)[0].cpu().numpy() * 100

        detected = []
        confidence = {}

        for i, cls in enumerate(class_names):
            score = round(float(probs[i]), 2)
            confidence[cls] = score

            if cls == "wrinkles":
                if score >= wrinkle_threshold:
                    detected.append(cls)
            else:
                if score >= disease_threshold:
                    detected.append(cls)

        return {
            "success": True,
            "detected_classes": detected,
            "confidence_scores": confidence
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Prediction failed: {str(e)}"
        )