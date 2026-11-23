from datetime import date, datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session, aliased

from app.db.database import get_db
from app.fair.services import fare_data_status
from app.monitoring.model import AdminAuditLog, FareLookup
from app.security import require_admin
from app.stops.model import Stop

router = APIRouter(prefix="/v1/admin", tags=["admin: monitoring"], dependencies=[Depends(require_admin)])


class DailyLookups(BaseModel):
    day: date
    lookups: int
    with_fare: int


class TopTrip(BaseModel):
    origin: str
    destination: str
    lookups: int


class FareDataAge(BaseModel):
    puv_type: str
    label: str
    effective_from: date | None
    age_days: int | None


class StatsSchema(BaseModel):
    days: int
    total_lookups: int
    success_rate: float | None      # share of lookups that returned a fare
    unsupported_rate: float | None  # share where no route connects the stops
    avg_response_ms: float | None
    daily: list[DailyLookups]
    top_trips: list[TopTrip]
    fare_data: list[FareDataAge]


class AuditEntry(BaseModel):
    admin_email: str
    method: str
    path: str
    status_code: int
    created_at: datetime


@router.get("/stats", response_model=StatsSchema)
def stats(session: Annotated[Session, Depends(get_db)], days: Annotated[int, Query(ge=1, le=365)] = 30):
    """
    KPIs for the last `days` days (Manila time): lookups, success and unsupported rates, response
    time, lookups per day, the most searched trips, and how old each fare matrix in effect is.
    """
    manila_day = cast(func.timezone("Asia/Manila", FareLookup.created_at), Date)
    since = cast(func.timezone("Asia/Manila", func.now()), Date) - (days - 1)
    in_range = manila_day >= since

    total, with_fare, unsupported, avg_ms = session.execute(
        select(
            func.count(),
            func.count().filter(FareLookup.has_fare),
            func.count().filter(FareLookup.route_count == 0),
            func.avg(FareLookup.duration_ms),
        ).where(in_range)
    ).one()

    daily = session.execute(
        select(manila_day.label("day"), func.count(), func.count().filter(FareLookup.has_fare))
        .where(in_range).group_by("day").order_by("day")
    ).all()

    origin, destination = aliased(Stop), aliased(Stop)
    top = session.execute(
        select(origin.name, destination.name, func.count().label("n"))
        .select_from(FareLookup)
        .join(origin, origin.id == FareLookup.origin_stop_id)
        .join(destination, destination.id == FareLookup.destination_stop_id)
        .where(in_range).group_by(origin.name, destination.name).order_by(func.count().desc()).limit(5)
    ).all()

    today = datetime.now(ZoneInfo("Asia/Manila")).date()
    return {
        "days": days,
        "total_lookups": total,
        "success_rate": with_fare / total if total else None,
        "unsupported_rate": unsupported / total if total else None,
        "avg_response_ms": float(avg_ms) if avg_ms is not None else None,
        "daily": [{"day": d, "lookups": n, "with_fare": f} for d, n, f in daily],
        "top_trips": [{"origin": o, "destination": d, "lookups": n} for o, d, n in top],
        "fare_data": [
            {
                "puv_type": s["puv_type"], "label": s["label"],
                "effective_from": s["fare_matrix"].effective_from if s["fare_matrix"] else None,
                "age_days": (today - s["fare_matrix"].effective_from).days if s["fare_matrix"] else None,
            }
            for s in fare_data_status(session)
        ],
    }


@router.get("/audit-log", response_model=list[AuditEntry])
def audit_log(session: Annotated[Session, Depends(get_db)], limit: Annotated[int, Query(ge=1, le=500)] = 100):
    """The latest admin changes, newest first."""
    return session.execute(
        select(AdminAuditLog).order_by(AdminAuditLog.created_at.desc()).limit(limit)
    ).scalars().all()
