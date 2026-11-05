import logging
import math
import uuid
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session, aliased

from app.fair.model import FareMatrix, SavedFare
from app.fair.schema import RouteMatchSchema
from app.route_point.model import RoutePoint
from app.routes.model import Route

logger = logging.getLogger(__name__)


def compute_fare(
    distance_km: Decimal, fares: dict[int, FareMatrix]
) -> tuple[Decimal, Decimal]:
    """
    Get the (regular, discounted) fare for a distance.
    Partial kilometers are rounded up, with a minimum of 1 km.
    """

    km = max(1, math.ceil(distance_km))

    if km in fares:
        return fares[km].regular_fare, fares[km].discounted_fare

    # ponytail: past the fare table, extend the guide's pattern (+P2/km, discounted = 80% to the nearest 25 centavos);
    # add rows to fare_matrix once the official table beyond its max km is known
    max_km = max(fares)
    regular = fares[max_km].regular_fare + 2 * (km - max_km)
    discounted = (regular * Decimal("0.8") * 4).quantize(Decimal(1)) / 4
    return regular, discounted.quantize(Decimal("0.01"))


def get_route_points(db: Session, start_point_id: uuid.UUID, end_point_id: uuid.UUID) -> list[dict]:
    """
    Get every route that contains both the start and end point (in either direction),
    with the route points from start to end in travel order.
    A result already saved for the stop pair is returned without searching again.
    """

    if start_point_id == end_point_id:
        raise HTTPException(status_code=400, detail="Start and end point must be different")

    # The same stop is stored once per route, so resolve the selected IDs to stop names
    # and match every route that has a stop with those names
    names = dict(
        db.execute(
            select(RoutePoint.id, RoutePoint.point_name).where(
                RoutePoint.id.in_([start_point_id, end_point_id])
            )
        ).all()
    )

    for point_id in (start_point_id, end_point_id):
        if point_id not in names:
            raise HTTPException(status_code=404, detail=f"Route point with ID {point_id} not found")

    start_name, end_name = names[start_point_id], names[end_point_id]

    saved = db.get(SavedFare, (start_name, end_name))
    if saved is not None:
        return saved.routes

    routes = search_routes(db, start_name, end_name)

    # Save only complete results: a route without a fare yet must be searched again once
    # its distances are filled (the DB triggers clear saved fares when route_points change)
    if all(route["regular_fare"] is not None for route in routes):
        try:
            # Two first-time requests for the same pair may race; the first insert wins
            db.execute(
                insert(SavedFare)
                .values(start_point_name=start_name, end_point_name=end_name, routes=routes)
                .on_conflict_do_nothing()
            )
            db.commit()
        except Exception:
            # Saving is an optimization; still answer the request if it fails
            db.rollback()
            logger.exception("Failed to save fare for %s -> %s", start_name, end_name)

    return routes


def search_routes(db: Session, start_name: str, end_name: str) -> list[dict]:
    """
    Run the route search and fare computation for two stop names.
    Returns JSON-ready dicts in the /fair/routes response shape, so they can be saved as-is.
    """

    origin = aliased(RoutePoint)
    destination = aliased(RoutePoint)

    matching_routes = (
        select(
            origin.route_id,
            origin.stop_sequence.label("origin_sequence"),
            destination.stop_sequence.label("destination_sequence"),
            func.least(origin.stop_sequence, destination.stop_sequence).label("low_sequence"),
            func.greatest(origin.stop_sequence, destination.stop_sequence).label("high_sequence"),
        )
        # Join the origin and destination points on the same route
        .join(
            destination,
            destination.route_id == origin.route_id,
        )
        # Filter only routes that contain both points, in any order
        # ponytail: a route listing the same stop name twice (loop) matches once per pair, dedupe if loops are added
        .where(
            origin.point_name == start_name,
            destination.point_name == end_name,
            origin.id != destination.id,
        )
    ).subquery()

    # Retrieve the stops between the origin and destination of each matching route.
    # Reversed trips (origin after destination) are ordered backwards so the list follows travel order.
    route_query = (
        select(RoutePoint, Route)
        .join(matching_routes, matching_routes.c.route_id == RoutePoint.route_id)
        .join(Route, Route.id == RoutePoint.route_id)
        .where(
            RoutePoint.stop_sequence.between(
                matching_routes.c.low_sequence, matching_routes.c.high_sequence
            )
        )
        .order_by(
            Route.route_name,
            Route.id,
            case(
                (
                    matching_routes.c.origin_sequence < matching_routes.c.destination_sequence,
                    RoutePoint.stop_sequence,
                ),
                else_=-RoutePoint.stop_sequence,
            ),
        )
    )

    # Group the flat rows into one entry per route
    routes: dict[uuid.UUID, dict] = {}
    for point, route in db.execute(route_query).all():
        routes.setdefault(
            route.id, {"route_id": route.id, "route_name": route.route_name, "points": []}
        )["points"].append(point)

    fares = {fare.distance_km: fare for fare in db.execute(select(FareMatrix)).scalars()}

    for route in routes.values():
        # Each stop stores the distance from the previous stop, so the trip distance
        # is the sum over every stop except the lowest-sequence one, in either direction
        first_stop = min(route["points"], key=lambda point: point.stop_sequence)
        segments = [p.distance_from_previous_km for p in route["points"] if p is not first_stop]

        # Distances not fetched yet: return the route without a fare instead of a wrong one
        if None in segments:
            route.update(distance_km=None, regular_fare=None, discounted_fare=None)
            continue

        distance = sum(segments, Decimal(0))
        regular, discounted = compute_fare(distance, fares)
        route.update(distance_km=distance, regular_fare=regular, discounted_fare=discounted)

    return [
        RouteMatchSchema.model_validate(route, from_attributes=True).model_dump(mode="json")
        for route in routes.values()
    ]
