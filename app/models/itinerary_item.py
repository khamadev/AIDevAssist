from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    trip_id: Mapped[int] = mapped_column(ForeignKey("trips.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    day: Mapped[date] = mapped_column(Date, nullable=False)

    trip: Mapped["Trip"] = relationship(back_populates="itinerary_items")
