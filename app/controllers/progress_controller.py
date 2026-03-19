"""
progress_controller.py
======================
Handles daily check-in and progress retrieval.

MongoDB collections used:
    plan_progress  → one document per plan per day
                     updated (upserted) each time user submits check-in
    plans          → read-only here — verify ownership + get checklist totals
"""

from datetime import datetime, timezone
from bson import ObjectId
from pymongo import ReturnDocument

from app.schemas.plan_schema import (
    CheckinRequest, CheckinResponse,
    ProgressResponse, DayProgress,
)
from app.db.mongodb import get_db


async def save_checkin(
    request: CheckinRequest,
    user_id: str,
) -> CheckinResponse:
    """
    Save (or update) daily check-in to plan_progress collection.

    Document structure in plan_progress collection:
    {
        plan_id:         string  (reference to plans._id),
        user_id:         string  (reference to users._id),
        day:             int     (1-7),
        completed_ids:   list    (checklist item IDs user ticked),
        completed_count: int,
        total_count:     int,
        completion_pct:  int,
        skin_rating:     int     (1-10),
        checked_at:      datetime,
    }

    Uses upsert — if user re-submits Day 1 it updates, not duplicates.
    Unique index on (plan_id, day) enforces one document per day per plan.
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    # 1. Validate plan exists and belongs to this user
    try:
        plan_oid = ObjectId(request.plan_id)
    except Exception:
        raise ValueError("Invalid plan_id format.")

    plan = await db["plans"].find_one(
        {"_id": plan_oid, "user_id": user_id},
        {"days": 1}   # only fetch days field — minimize data transfer
    )
    if not plan:
        raise ValueError("Plan not found or does not belong to you.")

    # 2. Find this day in the plan and count total tasks
    day_data = next(
        (d for d in plan.get("days", []) if d["day"] == request.day),
        None
    )
    if not day_data:
        raise ValueError(f"Day {request.day} not found in this plan.")

    total_count     = len(day_data.get("checklist", []))
    completed_count = len(request.completed_ids)

    # Safety check — cannot complete more than total
    if completed_count > total_count:
        completed_count = total_count

    completion_pct = round(
        (completed_count / total_count * 100) if total_count > 0 else 0
    )

    # 3. Upsert into plan_progress collection
    # upsert=True: creates if not exists, updates if exists (re-submission)
    progress_doc = {
        "plan_id":         request.plan_id,
        "user_id":         user_id,
        "day":             request.day,
        "completed_ids":   request.completed_ids,
        "completed_count": completed_count,
        "total_count":     total_count,
        "completion_pct":  completion_pct,
        "skin_rating":     request.skin_rating,
        "checked_at":      datetime.now(timezone.utc),
    }

    await db["plan_progress"].update_one(
        {"plan_id": request.plan_id, "day": request.day},
        {"$set": progress_doc},
        upsert=True
    )

    # 4. Build human-readable message
    if completion_pct == 100:
        message = f"Day {request.day} fully complete! Excellent work."
    elif completion_pct >= 70:
        message = f"Great effort! {completion_pct}% done for Day {request.day}."
    elif completion_pct >= 40:
        message = f"Good start. {completion_pct}% done — try to complete more tomorrow."
    else:
        message = f"Day {request.day} logged. Even small steps count — keep going."

    return CheckinResponse(
        status          = "success",
        day             = request.day,
        completed_count = completed_count,
        total_count     = total_count,
        completion_pct  = completion_pct,
        skin_rating     = request.skin_rating,
        message         = message,
    )


async def get_progress(
    plan_id: str,
    user_id: str,
) -> ProgressResponse:
    """
    Return 7-day progress summary by reading from plan_progress collection.

    Reads:
        plans collection         → get plan metadata + total tasks per day
        plan_progress collection → get check-in data per day
    """
    db = get_db()
    if db is None:
        raise RuntimeError("Database unavailable. Please try again later.")

    # 1. Validate plan exists and belongs to this user
    try:
        plan_oid = ObjectId(plan_id)
    except Exception:
        raise ValueError("Invalid plan_id format.")

    plan = await db["plans"].find_one(
        {"_id": plan_oid, "user_id": user_id},
        {"condition": 1, "days": 1, "plan_title": 1}
    )
    if not plan:
        raise ValueError("Plan not found or does not belong to you.")

    # 2. Fetch all check-ins for this plan from plan_progress
    cursor   = db["plan_progress"].find({"plan_id": plan_id})
    checkins = {}
    async for doc in cursor:
        checkins[doc["day"]] = doc   # keyed by day number

    # 3. Build per-day summary
    days_data       = plan.get("days", [])
    day_summaries   = []
    total_completed = 0
    total_tasks     = 0
    skin_ratings    = []
    days_checked    = 0

    for day_data in days_data:
        day_num  = day_data["day"]
        total    = len(day_data.get("checklist", []))
        checkin  = checkins.get(day_num)
        checked  = checkin is not None

        completed = checkin.get("completed_count", 0) if checkin else 0
        pct       = checkin.get("completion_pct", 0)  if checkin else 0
        rating    = checkin.get("skin_rating")         if checkin else None

        if checked:
            days_checked += 1
        if rating is not None:
            skin_ratings.append(rating)

        total_completed += completed
        total_tasks     += total

        day_summaries.append(DayProgress(
            day             = day_num,
            completed_count = completed,
            total_count     = total,
            completion_pct  = pct,
            skin_rating     = rating,
            checked_in      = checked,
        ))

    # 4. Calculate overall stats
    overall_pct = round(
        (total_completed / total_tasks * 100) if total_tasks > 0 else 0
    )
    avg_skin_rating = (
        round(sum(skin_ratings) / len(skin_ratings), 1)
        if skin_ratings else None
    )

    # 5. Build summary message
    if days_checked == 0:
        message = "You haven't started yet. Begin Day 1 today!"
    elif days_checked == 7:
        message = (
            f"You completed the full 7-day plan! "
            f"Overall {overall_pct}% of tasks done."
        )
    else:
        remaining = 7 - days_checked
        message   = (
            f"Day {days_checked} of 7 done. "
            f"{remaining} day{'s' if remaining > 1 else ''} remaining. Keep going!"
        )

    return ProgressResponse(
        status          = "success",
        plan_id         = plan_id,
        condition       = plan.get("condition", ""),
        overall_pct     = overall_pct,
        days_checked_in = days_checked,
        days            = day_summaries,
        avg_skin_rating = avg_skin_rating,
        message         = message,
    )