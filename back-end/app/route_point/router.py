
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.security import public_rate_limit, require_admin
from app.route_point import schema, service

router = APIRouter(
    prefix="/route-points",
    tags=["route-points"]
)

@router.get("/", response_model=list[schema.StopSchema], dependencies=[Depends(public_rate_limit)])
def list_stops(session: Annotated[Session, Depends(get_db)]):
    """
    List every known stop, one entry per stop name, sorted by name.

    :param session: SQLAlchemy session object
    :return: The known stops
    """
    return service.list_stops(session)


@router.post("/", response_model=schema.RoutePointResponseSchema, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin)])
def create_route_point(
    route_point_data: schema.RoutePointCreate,
    session: Annotated[Session, Depends(get_db)],
):
    """
    Create a new route point.

    :param route_point_data: RoutePointCreate object containing route point details
    :param session: SQLAlchemy session object
    :return: The created route point object
    """
    new_route_point = service.create_route_point(session, route_point_data)
    return new_route_point


@router.put("/{route_point_id}", response_model=schema.RoutePointResponseSchema, dependencies=[Depends(require_admin)])
def update_route_point(
    route_point_id: uuid.UUID,
    route_point_data: schema.RoutePointEdit,
    session: Annotated[Session, Depends(get_db)],
):
    """
    Update an existing route point.

    :param route_point_id: The ID of the route point to update
    :param route_point_data: RoutePointEdit object containing updated route point details
    :param session: SQLAlchemy session object
    :return: The updated route point object
    """
    updated_route_point = service.update_route_point(session, route_point_id, route_point_data)
    return updated_route_point


@router.delete("/{route_point_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
def delete_route_point(
    route_point_id: uuid.UUID, session: Annotated[Session, Depends(get_db)]
):
    """
    Delete a route point.

    :param route_point_id: The ID of the route point to delete
    :param session: SQLAlchemy session object
    """
    service.delete_route_point(session, route_point_id)
