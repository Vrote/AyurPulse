"""
chat.py — POST /api/v1/chat
----------------------------
JWT-protected endpoint for the AyurBot Ayurvedic Chatbot.
Automatically routes queries between general knowledge and
personalized plan data based on the user's question.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.controllers.chat_controller import handle_chat_message
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/api/v1",
    tags=["Ayurvedic Chatbot"],
)


class ChatPlanResponse(BaseModel):
    id: str = Field(..., description="The plan's MongoDB ObjectId as a string.")
    title: str = Field(..., description="Plan title")
    condition: str = Field(..., description="Skin condition associated with the plan")
    dosha: str = Field(..., description="Dosha associated with the plan")
    created_at: str = Field(..., description="Creation date formatted as YYYY-MM-DD")


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="The user's natural language Ayurvedic question.",
        examples=["What foods should I avoid for Pitta dosha?"],
    )
    history: list[dict] = Field(
        default=[],
        description="Previous messages in the conversation [{role, content}, ...]",
    )
    chat_mode: str = Field(
        default="general",
        description="Chat mode: general or plan",
    )
    plan_id: Optional[str] = Field(
        default=None,
        description="MongoDB ID of the selected plan when chat_mode is 'plan'",
    )


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Answer from AyurBot.")
    sources: list[str] = Field(
        default=[],
        description="References used to generate the answer.",
    )


@router.get(
    "/chat/plans",
    response_model=list[ChatPlanResponse],
    summary="Get user plans for chat context",
    description="Returns a list of all plans created by the logged-in user, to select as chat context."
)
async def chat_plans(
    current_user: dict = Depends(get_current_user),
):
    try:
        from app.controllers.chat_controller import get_user_plans_for_chat
        return await get_user_plans_for_chat(current_user["user_id"])
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch plans for chat: {str(e)}",
        )


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask AyurBot",
    description=(
        "Send a natural language question about Ayurveda or your personal wellness plan. "
        "AyurBot automatically determines whether to search your personalized plan data "
        "or the general Ayurvedic knowledge base. Requires login."
    ),
)
async def chat(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    AyurBot chatbot endpoint.
      1. Validates JWT via get_current_user dependency.
      2. Delegates to handle_chat_message(user_message, user_id).
      3. Intent is auto-detected internally.
      4. Returns { answer, sources }.
    """
    try:
        result = await handle_chat_message(
            user_message=request.message,
            user_id=current_user["user_id"],
            history=request.history,
            chat_mode=request.chat_mode,
            plan_id=request.plan_id,
        )
        return ChatResponse(
            answer=result["answer"],
            sources=result["sources"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chatbot error: {str(e)}",
        )

