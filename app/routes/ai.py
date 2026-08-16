from fastapi import APIRouter, HTTPException

from app.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIPlanDay,
    AIPlanItem,
)

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-itinerary", response_model=AIGenerateResponse)
def generate_itinerary(payload: AIGenerateRequest):
    if payload.days < 1 or payload.days > 14:
        raise HTTPException(status_code=400, detail="days must be between 1 and 14")

    days_plan = []
    for d in range(1, payload.days + 1):
        items = [
            AIPlanItem(
                title=f"Morning highlight in {payload.destination}",
                time="09:00",
                notes="Start early to avoid crowds",
            ),
            AIPlanItem(
                title=f"Lunch experience ({payload.preferences or 'local food'})",
                time="12:30",
                notes="Try a popular local restaurant",
            ),
            AIPlanItem(
                title="Evening walk / relax",
                time="18:00",
                notes="Flexible free time",
            ),
        ]
        days_plan.append(AIPlanDay(day=d, items=items))

    return AIGenerateResponse(days=days_plan)