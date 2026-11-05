from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.db.database import SessionLocal
from app.fair.model import FareMatrix, SavedFare
from app.fair.services import compute_fare
from app.main import app
from tests.conftest import ADMIN_HEADERS
from app.route_point.model import RoutePoint

client = TestClient(app, headers=ADMIN_HEADERS)

NON_EXISTENT_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def routes():
    # route_1: A -> B -> C -> D -> E, route_2: D -> X -> B (shares B and D, reversed), route_3: no shared pair
    stops = {"Fair 1": ["A", "B", "C", "D", "E"], "Fair 2": ["D", "X", "B"], "Fair 3": ["B", "Y"]}
    created = {}
    for route_name, names in stops.items():
        route_id = client.post("/routes/", json={"route_name": route_name}).json()["id"]
        created[route_name] = {"id": route_id, "points": {}}
        for seq, name in enumerate(names, 1):
            point = client.post("/route-points/", json={
                "route_id": route_id, "point_name": name, "stop_sequence": seq,
                "latitude": 14.65, "longitude": 121.10,
            }).json()
            created[route_name]["points"][name] = point["id"]
    yield created
    for route in created.values():
        client.delete(f"/routes/{route['id']}")


def search(start_id, end_id):
    return client.get("/fair/routes", params={"start_point_id": start_id, "end_point_id": end_id})


def summary(response):
    return [(r["route_name"], [p["point_name"] for p in r["points"]]) for r in response.json()]


def test_forward_and_reverse_routes(routes):
    response = search(routes["Fair 1"]["points"]["B"], routes["Fair 1"]["points"]["D"])
    assert response.status_code == 200
    assert summary(response) == [("Fair 1", ["B", "C", "D"]), ("Fair 2", ["B", "X", "D"])]


def test_reverse_input(routes):
    response = search(routes["Fair 1"]["points"]["D"], routes["Fair 1"]["points"]["B"])
    assert summary(response) == [("Fair 1", ["D", "C", "B"]), ("Fair 2", ["D", "X", "B"])]


def test_points_selected_from_another_route(routes):
    # IDs from route_2 still match route_1 because the stop names are shared
    response = search(routes["Fair 2"]["points"]["B"], routes["Fair 2"]["points"]["D"])
    assert summary(response) == [("Fair 1", ["B", "C", "D"]), ("Fair 2", ["B", "X", "D"])]


def test_no_route_contains_both(routes):
    response = search(routes["Fair 3"]["points"]["Y"], routes["Fair 1"]["points"]["E"])
    assert response.status_code == 200
    assert response.json() == []


def test_same_start_and_end(routes):
    point_id = routes["Fair 1"]["points"]["B"]
    assert search(point_id, point_id).status_code == 400


def test_point_not_found(routes):
    assert search(routes["Fair 1"]["points"]["B"], NON_EXISTENT_ID).status_code == 404


def test_invalid_point_id():
    assert search("invalid", NON_EXISTENT_ID).status_code == 422


def test_fare_matrix_follows_fare_guide_pattern():
    # Guards against typos in the fare_matrix migration: P14 for the first 4 km, +P2 per km after,
    # discounted = 80% of regular rounded to the nearest 25 centavos
    with SessionLocal() as db:
        fares = db.execute(select(FareMatrix).order_by(FareMatrix.distance_km)).scalars().all()

    assert [f.distance_km for f in fares] == list(range(1, 26))
    for fare in fares:
        regular = 14 + 2 * max(0, fare.distance_km - 4)
        assert fare.regular_fare == regular, fare.distance_km
        assert fare.discounted_fare == round(regular * 0.8 * 4) / 4, fare.distance_km


def set_distances(distances):
    with SessionLocal() as db:
        for point_id, km in distances.items():
            db.execute(update(RoutePoint).where(RoutePoint.id == point_id).values(distance_from_previous_km=km))
        db.commit()


def test_compute_fare_rounds_up():
    with SessionLocal() as db:
        fares = {fare.distance_km: fare for fare in db.execute(select(FareMatrix)).scalars()}

    assert compute_fare(Decimal("0.4"), fares) == (14, Decimal("11.25"))  # under 1 km -> 1 km
    assert compute_fare(Decimal("4.0"), fares) == (14, Decimal("11.25"))  # exact km stays
    assert compute_fare(Decimal("4.01"), fares) == (16, Decimal("12.75"))
    assert compute_fare(Decimal("25.0"), fares) == (56, Decimal("44.75"))
    assert compute_fare(Decimal("25.1"), fares) == (58, Decimal("46.50"))  # past the table
    assert compute_fare(Decimal("27.3"), fares) == (62, Decimal("49.50"))


def test_fare_in_search(routes):
    p1, p2 = routes["Fair 1"]["points"], routes["Fair 2"]["points"]
    set_distances({p1["B"]: "1.2", p1["C"]: "2.5", p1["D"]: "2.6", p1["E"]: "9"})

    for start, end in (("B", "D"), ("D", "B")):
        result = search(p1[start], p1[end]).json()
        fair_1 = next(r for r in result if r["route_name"] == "Fair 1")
        assert fair_1["distance_km"] == 5.1  # C + D segments, B's segment is before the trip
        assert (fair_1["regular_fare"], fair_1["discounted_fare"]) == (18, 14.50)  # 5.1 km -> 6 km

    # Fair 2 has no distances yet, so no fare instead of a wrong one
    fair_2 = next(r for r in search(p2["B"], p2["D"]).json() if r["route_name"] == "Fair 2")
    assert (fair_2["distance_km"], fair_2["regular_fare"], fair_2["discounted_fare"]) == (None, None, None)


def test_editing_a_stop_clears_route_distances(routes):
    route_id, points = routes["Fair 1"]["id"], routes["Fair 1"]["points"]
    set_distances({points["B"]: "1.2", points["C"]: "2.5"})

    client.put(f"/route-points/{points['C']}", json={
        "route_id": route_id, "point_name": "C", "stop_sequence": 3,
        "latitude": 14.66, "longitude": 121.11,
    })

    with SessionLocal() as db:
        distances = db.execute(
            select(RoutePoint.distance_from_previous_km).where(RoutePoint.route_id == route_id)
        ).scalars().all()
    assert distances == [None] * 5


def test_sto_nino_to_olopsc():
    # Copy of the real Marikina - SSS Village stretch with its OpenRouteService segment distances
    stops = [
        ("Sto. Nino", None), ("Savemore", "0.618"), ("2nd Street", "0.239"),
        ("Puregold - Conception", "1.572"), ("Meralco", "0.860"), ("OLOPSC", "0.456"),
    ]
    route_id = client.post("/routes/", json={"route_name": "Fair SSS Village copy"}).json()["id"]
    try:
        ids = {}
        for seq, (name, _) in enumerate(stops, 1):
            ids[name] = client.post("/route-points/", json={
                "route_id": route_id, "point_name": name, "stop_sequence": seq,
                "latitude": 14.65, "longitude": 121.10,
            }).json()["id"]
        set_distances({ids[name]: km for name, km in stops if km})

        for start, end in (("Sto. Nino", "OLOPSC"), ("OLOPSC", "Sto. Nino")):
            # Names match the real route too, so pick out the copy
            result = next(r for r in search(ids[start], ids[end]).json() if r["route_id"] == route_id)
            assert result["points"][0]["point_name"] == start
            assert len(result["points"]) == 6
            assert result["distance_km"] == 3.745
            assert (result["regular_fare"], result["discounted_fare"]) == (14, 11.25)  # 3.745 km -> 4 km
    finally:
        client.delete(f"/routes/{route_id}")


def saved_fare(start, end):
    with SessionLocal() as db:
        return db.get(SavedFare, (start, end))


def test_complete_result_is_saved_and_reused(routes):
    p1 = routes["Fair 1"]["points"]
    set_distances({p1["B"]: "1.2", p1["C"]: "2.5", p1["D"]: "2.6", p1["E"]: "9"})
    # Fair 1 only, so every route in the result has a fare
    first = search(p1["C"], p1["E"]).json()
    assert saved_fare("C", "E").routes == first

    # A hit returns the saved row without searching: prove it by tampering with the row
    with SessionLocal() as db:
        db.execute(update(SavedFare).where(SavedFare.start_point_name == "C").values(routes=[]))
        db.commit()
    assert search(p1["C"], p1["E"]).json() == []


def test_result_missing_a_fare_is_not_saved(routes):
    p1 = routes["Fair 1"]["points"]
    # Fair 2 also connects B and D but has no distances yet
    set_distances({p1["C"]: "2.5", p1["D"]: "2.6"})
    search(p1["B"], p1["D"])
    assert saved_fare("B", "D") is None


def test_editing_routes_clears_saved_fares(routes):
    p1 = routes["Fair 1"]["points"]
    set_distances({p1["D"]: "2.6", p1["E"]: "9"})
    search(p1["D"], p1["E"])
    assert saved_fare("D", "E") is not None

    # Any write to routes / route_points / fare_matrix clears every saved fare (DB trigger)
    client.put(f"/routes/{routes['Fair 3']['id']}", json={"route_name": "Fair 3 renamed"})
    assert saved_fare("D", "E") is None
