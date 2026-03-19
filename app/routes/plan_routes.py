from fastapi import APIRouter, HTTPException, Depends, status

from app.controllers.plan_controller import generate_plan, get_my_plan
from app.controllers.progress_controller import save_checkin, get_progress
from app.schemas.plan_schema import (
    SkinProfileRequest, PlanResponse,
    CheckinRequest, CheckinResponse,
    ProgressResponse,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1/plan",
    tags=["Ayurvedic Plan"]
)


# ── Generate plan ──────────────────────────────────────────────────────────────
@router.post(
    "/generate",
    response_model=PlanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate 7-day Ayurvedic plan",
    description=(
        "Fill the 9-field skin profile form. System selects the right plan "
        "from the dataset, personalizes it to your profile, saves it to your account, "
        "and returns all 7 days with a tickable checklist for each day. Requires login."
    ),
)
async def generate(
    profile: SkinProfileRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await generate_plan(profile, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except FileNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plan generation failed: {str(e)}"
        )


# ── Get my current plan ────────────────────────────────────────────────────────
@router.get(
    "/my-plan",
    summary="Get my current plan",
    description=(
        "Returns your most recent active plan with all 7 days and checklist. "
        "Use this to reload your plan when you open the app. Requires login."
    ),
)
async def my_plan(current_user: dict = Depends(get_current_user)):
    try:
        return await get_my_plan(current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch plan: {str(e)}"
        )


# ── Daily check-in ─────────────────────────────────────────────────────────────
@router.post(
    "/checkin",
    response_model=CheckinResponse,
    summary="Submit daily check-in",
    description=(
        "User submits which tasks they completed today and rates their skin 1-10. "
        "Send the list of completed checklist item IDs and the skin rating. "
        "Can be updated multiple times for the same day. Requires login."
    ),
)
async def checkin(
    data: CheckinRequest,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await save_checkin(data, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Check-in failed: {str(e)}"
        )


# ── Progress summary ───────────────────────────────────────────────────────────
@router.get(
    "/progress/{plan_id}",
    response_model=ProgressResponse,
    summary="Get 7-day progress",
    description=(
        "Returns your completion percentage and skin rating for each day. "
        "Frontend uses this to show the progress tracker. Requires login."
    ),
)
async def progress(
    plan_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        return await get_progress(plan_id, current_user["user_id"])
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not fetch progress: {str(e)}"
        )


# ── Conditions list ────────────────────────────────────────────────────────────
@router.get(
    "/conditions",
    summary="List supported conditions",
    description="Returns all 5 conditions. No login needed. Use to populate dropdown.",
)
async def conditions():
    return {
        "status": "success",
        "conditions": [
            {"value": "acne",        "label": "Acne",        "dosha": "Pitta"},
            {"value": "blackheads",  "label": "Blackheads",  "dosha": "Kapha"},
            {"value": "dark spots",  "label": "Dark Spots",  "dosha": "Pitta-Vata"},
            {"value": "pores",       "label": "Large Pores", "dosha": "Kapha"},
            {"value": "wrinkles",    "label": "Wrinkles",    "dosha": "Vata"},
        ]
    }