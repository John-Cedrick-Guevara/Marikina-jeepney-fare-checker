import uuid

from pydantic import BaseModel, Field

from app.route_point.schema import RoutePointResponseSchema


class FairSchema(BaseModel):
    id: uuid.UUID = Field(..., description="The ID of the route")

    point_a_id: str = Field(..., description="The ID of the point A")
    point_b_id: str = Field(..., description="The ID of the point B")

    classification: str = Field(..., description="The classification of the commuter")


class FairResponseSchema(BaseModel):
    route_stop_a_id: str = Field(..., description="The ID of the route stop")
    route_stop_b_id: str = Field(..., description="The ID of the route stop")
    fair: float = Field(..., description="The fair between the two route stops")
    discount: float = Field(
        ..., description="The discounted fair between the two route stops"
    )


class RouteMatchSchema(BaseModel):
    route_id: uuid.UUID = Field(..., description="The ID of the route")
    route_name: str = Field(..., description="The name of the route")
    points: list[RoutePointResponseSchema] = Field(
        ..., description="The route points from start to end in travel order"
    )
    distance_km: float | None = Field(
        ..., description="The road distance from start to end, null if not fetched yet"
    )
    regular_fare: float | None = Field(..., description="The regular fare")
    discounted_fare: float | None = Field(
        ..., description="The student / elderly / PWD fare"
    )
