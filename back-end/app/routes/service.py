
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.routes import schema
from app.routes.model import Route


def create_route(session: Session, route_data: schema.RouteCreate) -> Route:
    new_route = Route(
        route_name=route_data.route_name
    )

    session.add(new_route)

    try:
        session.commit()
        session.refresh(new_route)
    except Exception:
        session.rollback()
        raise

    return new_route


def delete_route(session: Session, route_id: str) -> None:
    route_to_delete = session.get(Route, route_id)

    if route_to_delete is None:
        raise HTTPException(
            status_code=404,
            detail=f"Route with ID {route_id} not found"
        )

    try:
        session.delete(route_to_delete)
        session.commit()
    except Exception:
        session.rollback()
        raise


def update_route(
    session: Session,
    route_id: str,
    route_data: schema.RouteEdit
) -> Route:
    route_to_update = session.get(Route, route_id)

    if route_to_update is None:
        raise HTTPException(
            status_code=404,
            detail=f"Route with ID {route_id} not found"
        )

    route_to_update.route_name = route_data.route_name

    try:
        session.commit()
        session.refresh(route_to_update)
    except Exception:
        session.rollback()
        raise

    return route_to_update
