from fastapi import APIRouter, HTTPException

from app.schemas import (
    AIGenerateRequest,
    AIGenerateResponse,
    AIPlanDay,
    AIPlanItem,
)
from app.services import poi

router = APIRouter(prefix="/ai", tags=["ai"])


class _PoiPicker:
    """Rotates through a destination's real POIs by category, so a
    multi-day itinerary doesn't repeat the same place until every option
    in that category has been used once.
    """

    def __init__(self, pois: list[dict]):
        self._by_category: dict[str, list[str]] = {}
        for item in pois:
            self._by_category.setdefault(item["category"], []).append(item["name"])
        self._cursor: dict[str, int] = {}

    def next(self, category: str) -> str | None:
        names = self._by_category.get(category)
        if not names:
            return None
        index = self._cursor.get(category, 0)
        self._cursor[category] = index + 1
        return names[index % len(names)]


@router.post("/generate-itinerary", response_model=AIGenerateResponse)
def generate_itinerary(payload: AIGenerateRequest):
    if payload.days < 1 or payload.days > 14:
        raise HTTPException(status_code=400, detail="days must be between 1 and 14")

    picker = _PoiPicker(_find_pois(payload.destination))
    evening_category = "nature" if "nature" in _preferred_categories(payload.preferences) else "sight"

    days_plan = []
    for d in range(1, payload.days + 1):
        items = [
            _build_item(
                picker,
                category="sight",
                slot_label="Morning",
                time="09:00",
                destination=payload.destination,
                fallback_title=f"Morning highlight in {payload.destination}",
                fallback_notes="Start early to avoid crowds",
            ),
            _build_item(
                picker,
                category="food",
                slot_label="Lunch",
                time="12:30",
                destination=payload.destination,
                fallback_title=f"Lunch experience ({payload.preferences or 'local food'})",
                fallback_notes="Try a popular local restaurant",
            ),
            _build_item(
                picker,
                category=evening_category,
                slot_label="Evening",
                time="18:00",
                destination=payload.destination,
                fallback_title="Evening walk / relax",
                fallback_notes="Flexible free time",
            ),
        ]
        days_plan.append(AIPlanDay(day=d, items=items))

    return AIGenerateResponse(days=days_plan)


def _find_pois(destination: str) -> list[dict]:
    coords = poi.geocode(destination)
    if not coords:
        return []
    lat, lon = coords
    return poi.fetch_points_of_interest(lat, lon)


def _preferred_categories(preferences: str) -> set[str]:
    text = preferences.lower()
    categories = set()
    if any(word in text for word in ("food", "restaurant", "cuisine", "eat")):
        categories.add("food")
    if any(word in text for word in ("nature", "park", "outdoor", "hike")):
        categories.add("nature")
    if any(word in text for word in ("museum", "history", "culture", "art")):
        categories.add("sight")
    return categories


def _build_item(
    picker: _PoiPicker,
    category: str,
    slot_label: str,
    time: str,
    destination: str,
    fallback_title: str,
    fallback_notes: str,
) -> AIPlanItem:
    name = picker.next(category)
    if name:
        return AIPlanItem(
            title=name,
            time=time,
            notes=f"{slot_label} suggestion near {destination}",
        )
    return AIPlanItem(title=fallback_title, time=time, notes=fallback_notes)
