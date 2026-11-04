from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base

class Fair(Base):
    __tablename__ = "fairs"

    id: Mapped[UUID] = mapped_column(UUID, primary_key=True)

    route_a_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("routes.id"))
    route_b_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("routes.id"))

    fair: Mapped[float] = mapped_column(Float, nullable=False)
    discount: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
