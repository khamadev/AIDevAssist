from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.deps import get_current_user
from app.models.itinerary_item import ItineraryItem
from app.models.trip import Trip
from app.models.user import User
from app.schemas import ItineraryItemCreate, ItineraryItemOut
from app.trip_logic import is_day_within_trip

router = APIRouter(prefix="/trips/{trip_id}/itinerary", tags=["itinerary"])


def _get_owned_trip(trip_id: int, db: Session, current_user: User) -> Trip:
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.owner_id == current_user.id).first()
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.post("", response_model=ItineraryItemOut, status_code=status.HTTP_201_CREATED)
def add_itinerary_item(
    trip_id: int,
    payload: ItineraryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trip = _get_owned_trip(trip_id, db, current_user)

    if not is_day_within_trip(payload.day, trip.start_date, trip.end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Itinerary item day must fall within the trip's date range",
        )

    item = ItineraryItem(trip_id=trip.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("", response_model=list[ItineraryItemOut])
def list_itinerary_items(
    trip_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    trip = _get_owned_trip(trip_id, db, current_user)
    return trip.itinerary_items
