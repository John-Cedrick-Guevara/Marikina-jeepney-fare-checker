import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.route_point.model import RoutePoint


def get_route_poins(db: Session, route_a_id: uuid.UUID, route_b_id: uuid.UUID) -> list[RoutePoint]:
    """
    Get the route points from point a to b for a specific route.
    """

    origin = aliased(RoutePoint)
    destination = aliased(RoutePoint)

    mathing_routes_query = (
        select(
            origin.route_id,
            origin.stop_sequence.label("origin_sequence"),
            destination.stop_sequence.label("destination_sequence"),
        )
        # Join the origin and destination points on the same route
        .join(
            destination,
            destination.route_id == origin.route_id,
        )
        # Filter only where the origin and destination points are on the same route and the origin sequence comes before the destination sequence
        .where(
            origin.route_id == route_a_id,
            destination.route_id == route_b_id,
            origin.stop_sequence < destination.stop_sequence,
        )
    )

    # Create a subquery of the matching routes
    matching_routes = mathing_routes_query.subquery()

    # Retrieve all stops belonging to those matching routes.
    # Join the original RoutePoint table with the temporary subquery
    # using route_id.
    route_query = (
        select(RoutePoint)
        .join(
            matching_routes,
            matching_routes.c.route_id == RoutePoint.route_id,
        )
        # Filter only where the sequence is between the origin and destination sequences
        .where(
            matching_routes.c.origin_sequence <= RoutePoint.stop_sequence,
            matching_routes.c.destination_sequence >= RoutePoint.stop_sequence,
        )
        # Order by the route id and the sequence
        .order_by(RoutePoint.route_id, RoutePoint.stop_sequence)
    )

    routes = db.execute(route_query).scalars().all()

    return routes
