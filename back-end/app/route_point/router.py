
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.route_point import schema, service

router = APIRouter(
    prefix="/route-points",
    tags=["route-points"]
)

@router.post("/", response_model=schema.RoutePointCreate, status_code=status.HTTP_201_CREATED)
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


@router.put("/{route_point_id}", response_model=schema.RoutePointEdit)
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


@router.delete("/{route_point_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route_point(
    route_point_id: uuid.UUID, session: Annotated[Session, Depends(get_db)]
):
    """
    Delete a route point.

    :param route_point_id: The ID of the route point to delete
    :param session: SQLAlchemy session object
    """
    service.delete_route_point(session, route_point_id)
