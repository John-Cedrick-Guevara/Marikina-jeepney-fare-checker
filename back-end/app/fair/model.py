from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class FareMatrix(Base):
    __tablename__ = "fare_matrix"

    distance_km: Mapped[int] = mapped_column(Integer, primary_key=True)

    regular_fare: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    # Student / elderly / PWD fare
    discounted_fare: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class SavedFare(Base):
    """A /fair/routes result saved for a stop pair; cleared by DB triggers when routes or fares change."""

    __tablename__ = "saved_fares"

    start_point_name: Mapped[str] = mapped_column(String, primary_key=True)
    end_point_name: Mapped[str] = mapped_column(String, primary_key=True)

    routes: Mapped[list[dict]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
