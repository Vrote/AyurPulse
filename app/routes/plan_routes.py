from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, List

from app.controllers.plan_controller import (
    generate_personalized_plan, 
    get_plan_history, 
    get_all_plans_for_doctor, 
    get_reviewed_plans_for_doctor,
    review_plan_by_doctor
)
from app.schemas.plan_schema import PlanRequest, PlanResponse, PlanReviewRequest
from app.auth.dependencies import get_current_user
from app.utils.prakriti_assessment import get_all_questions

router = APIRouter(
    prefix="/api/v1/plan",
    tags=["Ayurvedic Plans"]
)


@router.get(
    "/questions",
    summary="Get Dosha Assessment Questions",
    description="Returns the 6 questions needed for the Quick-6 Dosha Assessment."
)
async def fetch_questions():
    """Retrieve the static list of 6 Prakriti questions for the frontend."""
    return get_all_questions()


@router.post(
    "/generate",
    response_model=PlanResponse,
    summary="Generate personalized 7-day plan",
    description=(
        "Send prediction_id and user profile (Dosha, Skin Type, Lifestyle). "
        "Returns a personalized 7-day routine. Saves it to history. Requires login."
    )
)
async def create_plan(
    request: PlanRequest,
    current_user: dict = Depends(get_current_user)
):
    """Bridge between frontend form and backend Plan Assembly Engine."""
    try:
        return await generate_personalized_plan(request, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan generation failed: {str(e)}"
        )


@router.get(
    "/history",
    summary="Get plan history",
    description="Returns your last 5 generated plans. Requires login."
)
async def plan_history(
    current_user: dict = Depends(get_current_user)
):
    """Fetch user's saved plans from user_plans collection."""
    try:
        return await get_plan_history(current_user["user_id"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch history: {str(e)}"
        )


@router.get(
    "/unchecked-plans",
    summary="[Doctor Only] Get new/unchecked plans",
    description="Fetch every plan that is currently waiting for professional review. Requires Doctor role."
)
async def fetch_unchecked_plans(
    current_user: dict = Depends(get_current_user)
):
    """Doctor-only endpoint to see all system generated plans."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctors only."
        )
    return await get_all_plans_for_doctor(current_user.get("specialization"))


@router.get(
    "/reviewed-plans",
    summary="[Doctor Only] Get reviewed/checked plans",
    description="Returns a list of all plans already reviewed and approved by doctors. Useful for tracking history."
)
async def fetch_reviewed_plans(
    current_user: dict = Depends(get_current_user)
):
    """Doctor-only endpoint to see all plans that have already been reviewed."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctors only."
        )
    return await get_reviewed_plans_for_doctor(current_user.get("specialization"))


@router.patch(
    "/{plan_id}/review",
    summary="[Doctor Only] Review and Approve/Modify a plan",
    description="Update a plan with doctor notes or modifications. Sets 'is_doctor_vetted' flag."
)
async def review_plan(
    plan_id: str,
    request: PlanReviewRequest,
    current_user: dict = Depends(get_current_user)
):
    """Bridge for doctors to validate or change system plans."""
    if current_user.get("role") != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Doctors only."
        )
    
    try:
        return await review_plan_by_doctor(plan_id, request, current_user.get("full_name", "Doctor"))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review plan: {str(e)}"
        )
