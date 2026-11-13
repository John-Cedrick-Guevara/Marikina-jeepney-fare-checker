import logging
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.database import Base, SessionLocal

logger = logging.getLogger(__name__)


class FareLookup(Base):
    """One fare estimate a commuter requested (no IP or personal data)."""

    __tablename__ = "fare_lookups"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    origin_stop_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    destination_stop_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    puv_type: Mapped[str] = mapped_column(String, nullable=False)
    route_count: Mapped[int] = mapped_column(Integer, nullable=False)
    has_fare: Mapped[bool] = mapped_column(Boolean, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminAuditLog(Base):
    """One change an admin made."""

    __tablename__ = "admin_audit_log"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    admin_user_id: Mapped[uuid.UUID] = mapped_column(PG_UUID(as_uuid=True), nullable=False)
    admin_email: Mapped[str] = mapped_column(String, nullable=False)
    method: Mapped[str] = mapped_column(String, nullable=False)
    path: Mapped[str] = mapped_column(String, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def record_lookup(db: Session, response: dict, duration_ms: int) -> None:
    """Log a fare estimate for the KPI dashboard. Never fails the commuter's request."""
    routes = response["routes"]
    try:
        db.add(FareLookup(
            origin_stop_id=response["origin_stop_id"], destination_stop_id=response["destination_stop_id"],
            puv_type=response["puv_type"], route_count=len(routes),
            has_fare=any(route["regular_fare"] is not None for route in routes), duration_ms=duration_ms,
        ))
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to record fare lookup")


def record_admin_action(admin, method: str, path: str, status_code: int) -> None:
    """Write an admin change to the audit log, in its own session (the request's is closed by now)."""
    try:
        with SessionLocal() as db:
            db.add(AdminAuditLog(
                admin_user_id=admin.user_id, admin_email=admin.email, method=method, path=path,
                status_code=status_code,
            ))
            db.commit()
    except Exception:
        # Still visible in the server logs if the database write fails
        logger.exception("Failed to audit %s %s by %s (%s)", method, path, admin.email, status_code)
