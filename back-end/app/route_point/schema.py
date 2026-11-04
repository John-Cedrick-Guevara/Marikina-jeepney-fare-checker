import uuid

from pydantic import BaseModel, Field


class RoutePointSchema(BaseModel):
    route_id: uuid.UUID = Field(..., description="The ID of the route")

    point_name: str = Field(..., description="The name of the route point")

    stop_sequence: int = Field(..., description="The sequence of the route point")

    latitude: float = Field(..., ge=-90, le=90, description="The latitude of the route point")
    longitude: float = Field(..., ge=-180, le=180, description="The longitude of the route point")

class RoutePointResponseSchema(RoutePointSchema):
    id: uuid.UUID = Field(..., description="The ID of the route point")
    
class RoutePointCreate(RoutePointSchema):
    pass

class RoutePointEdit(RoutePointSchema):
    pass

class RoutePOintDelete(RoutePointSchema):
    pass

