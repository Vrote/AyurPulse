from fastapi import APIRouter, UploadFile, File, HTTPException, Depends

from app.controllers.prediction_controller import predict_skin_condition
from app.schemas.prediction_schema import PredictionResponse
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1",
    tags=["Skin Analysis"]
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Analyze skin image",
    description=(
        "Upload a facial skin image (JPG / PNG, max 5 MB). "
        "AI model detects: acne, blackheads, dark spots, pores, wrinkles. "
        "Result is saved to your account history. Requires login."
    ),
)
async def predict(
    file: UploadFile = File(..., description="Facial skin image — JPG or PNG, max 5 MB"),
    current_user: dict = Depends(get_current_user),
):
    # 1. Validate file type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. Upload JPG or PNG."
        )

    # 2. Read bytes
    image_bytes = await file.read()
    if len(image_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # 3. Run prediction — pass user_id so result is saved to their account
    try:
        return await predict_skin_condition(
            image_bytes = image_bytes,
            filename    = file.filename,
            user_id     = current_user["user_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@router.get(
    "/predict/history",
    summary="Get prediction history",
    description="Returns your last 10 skin analysis results. Requires login.",
)
async def prediction_history(
    current_user: dict = Depends(get_current_user),
):
    """Fetch user's last 10 predictions from skin_predictions collection."""
    from app.db.mongodb import get_db
    db = get_db()
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable.")

    cursor = db["skin_predictions"].find(
        {"user_id": current_user["user_id"]},
        {"_id": 0, "filename": 0}   # exclude internal fields
    ).sort("created_at", -1).limit(10)

    history = []
    async for doc in cursor:
        doc["created_at"] = doc["created_at"].isoformat()
        history.append(doc)

    return {
        "status":  "success",
        "count":   len(history),
        "history": history,
    }


@router.get(
    "/health",
    summary="Health check",
    description="Returns API status. No login needed.",
)
async def health_check():
    return {"status": "ok", "service": "AyurPulse Skin Analysis API"}