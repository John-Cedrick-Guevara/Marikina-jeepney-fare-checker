import uuid

from pydantic import BaseModel, Field


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
