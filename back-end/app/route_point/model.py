import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Float, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.routes import model as _routes_model  # noqa: F401  registers "routes" for the route_id FK


class RoutePoint(Base):
    __tablename__ = "route_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    route_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("routes.id")
    )

    point_name: Mapped[str] = mapped_column(String, nullable=False)

    stop_sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Road distance from the previous stop; null until scripts/fill_segment_distances.py fetches it
    distance_from_previous_km: Mapped[Decimal | None] = mapped_column(Numeric(7, 3))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

