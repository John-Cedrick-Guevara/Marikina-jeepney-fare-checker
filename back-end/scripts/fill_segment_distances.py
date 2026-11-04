"""
Fill route_points.distance_from_previous_km with the OpenRouteService (HeiGIT) road distance.

Only segments without a distance are fetched, so re-running costs no requests
once every route is captured. Run from back-end/: python -m scripts.fill_segment_distances
"""

import itertools
import os
import sys
import time
from decimal import Decimal

import httpx
from sqlalchemy import select

from app.db.database import SessionLocal
from app.route_point.model import RoutePoint

DIRECTIONS_API_URL = "https://api.openrouteservice.org/v2/directions/driving-car"

# ponytail: per-run safety cap, well under the free 2,000/day quota; raise it if a bulk import needs more
MAX_REQUESTS = 200


# The free plan allows 40 directions requests per minute
REQUEST_INTERVAL_SECONDS = 1.6


def fetch_distance_km(client: httpx.Client, api_key: str, origin: RoutePoint, destination: RoutePoint) -> Decimal:
    """
    Get the driving distance between two stops in km.
    OpenRouteService takes coordinates as [longitude, latitude].
    """

    response = client.post(
        DIRECTIONS_API_URL,
        headers={"Authorization": api_key},
        json={
            "coordinates": [
                [origin.longitude, origin.latitude],
                [destination.longitude, destination.latitude],
            ],
        },
    )
    if response.is_error:
        raise RuntimeError(
            f"{origin.point_name} -> {destination.point_name}: HTTP {response.status_code} {response.text[:200]}"
        )

    routes = response.json().get("routes")
    if not routes:
        raise RuntimeError(f"No route found from {origin.point_name} to {destination.point_name}")

    # Distance is in meters; omitted when origin and destination are the same spot
    return Decimal(str(routes[0]["summary"].get("distance", 0))) / 1000


def main() -> None:
    api_key = os.getenv("HEIGIT_KEY")
    if not api_key:
        sys.exit("HEIGIT_KEY is not set in .env")

    with SessionLocal() as db, httpx.Client(timeout=15) as client:
        points = db.execute(
            select(RoutePoint).order_by(RoutePoint.route_id, RoutePoint.stop_sequence)
        ).scalars().all()

        # Pair each stop with the previous stop on the same route, keeping only missing distances
        missing = [
            (previous, point)
            for previous, point in itertools.pairwise(points)
            if previous.route_id == point.route_id and point.distance_from_previous_km is None
        ]

        print(f"{len(missing)} segment(s) missing a distance")
        if len(missing) > MAX_REQUESTS:
            sys.exit(f"Refusing to send more than {MAX_REQUESTS} requests in one run")

        for previous, point in missing:
            time.sleep(REQUEST_INTERVAL_SECONDS)
            point.distance_from_previous_km = fetch_distance_km(client, api_key, previous, point)
            # Commit per segment so a failure midway keeps the requests already paid for
            db.commit()
            print(f"  {previous.point_name} -> {point.point_name}: {point.distance_from_previous_km} km")


if __name__ == "__main__":
    main()
