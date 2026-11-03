from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.routes import schema
from app.routes import service
import uuid


router = APIRouter(
    prefix="/routes",
    tags=["routes"]
)

@router.post("/", response_model=schema.RouteCreate, status_code=status.HTTP_201_CREATED)
def create_route(route_data: schema.RouteCreate, session: Session = Depends(get_db)):
    """
    Create a new route.

    :param route_data: RouteCreate object containing route details
    :param session: SQLAlchemy session object
    :return: The created route object
    """

    new_route = service.create_route(session, route_data)
    return new_route


@router.delete("/{route_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_route(route_id: uuid.UUID, session: Session = Depends(get_db)):
    """
    Delete a route by its ID.

    :param route_id: The ID of the route to delete
    :param session: SQLAlchemy session object
    """
    return service.delete_route(session, route_id)
    

@router.put("/{route_id}", response_model=schema.RouteEdit, status_code=status.HTTP_200_OK)
def update_route(route_id: uuid.UUID, route_data: schema.RouteEdit, session: Session = Depends(get_db)):
    """
    Update an existing route by its ID.

    :param route_id: The ID of the route to update
    :param route_data: RouteCreate object containing updated route details
    :param session: SQLAlchemy session object
    :return: The updated route object
    """
    
    return service.update_route(session, route_id, route_data)
   

