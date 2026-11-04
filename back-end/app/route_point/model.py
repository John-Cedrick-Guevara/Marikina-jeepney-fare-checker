from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass

class RoutePoint(Base):
    __tablename__ = "route_points"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)
    route_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("routes.id"))

    point_name: Mapped[str] = mapped_column(String, nullable=False)

    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

