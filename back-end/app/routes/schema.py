import uuid

from pydantic import BaseModel, Field


class RouteSchema(BaseModel):
    route_name: str = Field(..., min_length=1, description="The name of the route")

class RouteResponseSchema(RouteSchema):
     id: uuid.UUID = Field(..., description="The ID of the route")

class RouteCreate(RouteSchema):
    pass

class RouteEdit(RouteSchema):
    pass    

class RouteDelete(RouteSchema):
    pass


