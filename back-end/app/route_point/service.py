from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.route_point import schema
from app.route_point.model import RoutePoint


def create_route_point(session: Session, route_point_data: schema.RoutePointCreate) -> RoutePoint:
    new_route_point = RoutePoint(
        route_id=route_point_data.route_id,
        point_name=route_point_data.point_name,
        stop_sequence=route_point_data.stop_sequence,
        latitude=route_point_data.latitude,
        longitude=route_point_data.longitude
    )

    session.add(new_route_point)

    try:
        session.commit()
        session.refresh(new_route_point)
    except Exception:
        session.rollback()
        raise

    return new_route_point

def update_route_point(
    session: Session,
    route_point_id: str,
    route_point_data: schema.RoutePointEdit
) -> RoutePoint:
    route_point_to_update = session.get(RoutePoint, route_point_id)

    if route_point_to_update is None:
        raise HTTPException(
            status_code=404,
            detail=f"Route point with ID {route_point_id} not found"
        )

    for field, value in route_point_data.model_dump(exclude_unset=True).items():
        setattr(route_point_to_update, field, value)

    try:
        session.commit()
        session.refresh(route_point_to_update)
    except Exception:
        session.rollback()
        raise

    return route_point_to_update

def delete_route_point(session: Session, route_point_id: str) -> None:
    route_point_to_delete = session.get(RoutePoint, route_point_id)

    if route_point_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Route point with ID {route_point_id} not found"
        )

    try:
        session.delete(route_point_to_delete)
        session.commit()
    except Exception:
        session.rollback()
        raise

