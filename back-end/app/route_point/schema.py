import uuid

from pydantic import BaseModel, Field


class RoutePointSchema(BaseModel):
    route_id: uuid.UUID = Field(..., description="The ID of the route")

    point_name: str = Field(..., description="The name of the route point")

    stop_sequence: int = Field(..., description="The sequence of the route point")

    latitude: float = Field(..., description="The latitude of the route point")
    longitude: float = Field(..., description="The longitude of the route point")

    created_at: str = Field(
        ..., description="The date and time the route point was created"
    )
    updated_at: str = Field(
        ..., description="The date and time the route point was last updated"
    )

class RoutePointResponseSchema(RoutePointSchema):
    id: uuid.UUID = Field(..., description="The ID of the route point")
    
class RoutePointCreate(RoutePointSchema):
    pass

class RoutePointEdit(RoutePointSchema):
    pass

class RoutePOintDelete(RoutePointSchema):
    pass

