# app/routes/prediction_routes.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from app.controllers.prediction_controller import predict_skin

router = APIRouter()

@router.post("/predict")
async def predict(file: UploadFile = File(...), background_tasks: BackgroundTasks = BackgroundTasks()):
    """
    Upload an image file to get skin disease predictions.
    Automatically deletes the uploaded file after prediction.
    """
    try:
        # Call the async controller function
        result = await predict_skin(file, background_tasks)
        return {"success": True, "data": result}
    except HTTPException as he:
        # Re-raise HTTP exceptions (like invalid file type)
        raise he
    except Exception as e:
        # Catch-all for unexpected errors
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")