import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.security import public_rate_limit
from app.fair import schema, services

router = APIRouter(
    prefix="/fair",
    tags=["fair"],
    dependencies=[Depends(public_rate_limit)],
)

@router.get("/routes", response_model=list[schema.RouteMatchSchema], status_code=status.HTTP_200_OK)
def get_routes_between_points(
    start_point_id: uuid.UUID,
    end_point_id: uuid.UUID,
    session: Annotated[Session, Depends(get_db)],
):
    """
    Get every route that contains both points, with the route points from start to end.

    :param start_point_id: The ID of the selected start route point
    :param end_point_id: The ID of the selected end route point
    :param session: SQLAlchemy session object
    :return: The matching routes and their route points in travel order
    """
    return services.get_route_points(session, start_point_id, end_point_id)
