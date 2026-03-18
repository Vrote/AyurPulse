from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from app.controllers.prediction_controller import predict_skin_condition
from app.schemas.prediction_schema import PredictionResponse

router = APIRouter(
    prefix="/api/v1",
    tags=["Skin Analysis"]
)

# Allowed image types
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Analyze skin image",
    description=(
        "Upload a facial skin image (JPG / PNG). "
        "The model will detect one or more of: acne, blackheads, dark spots, pores, wrinkles."
    )
)
async def predict(
    file: UploadFile = File(..., description="Facial skin image (JPG or PNG, max 5 MB)")
):
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Please upload a JPG or PNG image."
        )

    # Read file bytes
    image_bytes = await file.read()

    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Run prediction
    try:
        result = await predict_skin_condition(image_bytes, file.filename)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get(
    "/health",
    summary="Health check",
    description="Returns API status. Use this to confirm the server is running."
)
async def health_check():
    return {"status": "ok", "service": "AyurPulse Skin Analysis API"}