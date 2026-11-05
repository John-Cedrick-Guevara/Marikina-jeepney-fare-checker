import pytest
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import ADMIN_HEADERS

client = TestClient(app, headers=ADMIN_HEADERS)

NON_EXISTENT_ID = "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def route_id():
    # route_points.route_id is a FK, so each test gets a throwaway route (cascade-deletes its points)
    route = client.post("/routes/", json={"route_name": "Test Route"}).json()
    yield route["id"]
    client.delete(f"/routes/{route['id']}")


def point(route_id=NON_EXISTENT_ID, **overrides):
    return {
        "route_id": route_id,
        "point_name": "Test Point",
        "stop_sequence": 1,
        "latitude": 12.345678,
        "longitude": 98.765432,
        **overrides,
    }


def test_edit_route_point_missing_fields():
    response = client.put(
        f"/route-points/{NON_EXISTENT_ID}",
        json={}
    )
    assert response.status_code == 422

def test_delete_route_point_missing_id():
    response = client.delete("/route-points/")
    assert response.status_code == 405

def test_update_route_point_id_not_found():
    response = client.put(
        f"/route-points/{NON_EXISTENT_ID}",
        json=point(point_name="Updated Point")
    )
    assert response.status_code == 404

def test_delete_route_point_id_not_found():
    response = client.delete(f"/route-points/{NON_EXISTENT_ID}")
    assert response.status_code == 404

def test_update_route_point_missing_id():
    response = client.put("/route-points/", json=point(point_name="Updated Point"))
    assert response.status_code == 405

def test_delete_route_point_invalid_id():
    response = client.delete("/route-points/invalid_point_id")
    assert response.status_code == 422

def test_update_route_point_invalid_id():
    response = client.put(
        "/route-points/invalid_point_id",
        json=point(point_name="Updated Point")
    )
    assert response.status_code == 422

def test_create_route_point(route_id):
    point_data = point(route_id)
    response = client.post("/route-points/", json=point_data)
    assert response.status_code == 201
    data = response.json()
    assert data["point_name"] == point_data["point_name"]
    assert data["latitude"] == point_data["latitude"]
    assert data["longitude"] == point_data["longitude"]

def test_create_route_point_missing_fields():
    response = client.post("/route-points/", json={})
    assert response.status_code == 422

def test_create_route_point_invalid_latitude():
    response = client.post("/route-points/", json=point(latitude=200.0))
    assert response.status_code == 422

def test_create_route_point_invalid_longitude():
    response = client.post("/route-points/", json=point(longitude=200.0))
    assert response.status_code == 422

def test_edit_route_point(route_id):
    # First, create a route point to edit
    create_response = client.post("/route-points/", json=point(route_id, point_name="Original Point"))
    assert create_response.status_code == 201
    point_id = create_response.json()["id"]

    # Now, edit the route point
    updated_data = point(
        route_id,
        point_name="Updated Point",
        latitude=23.456789,
        longitude=87.654321,
    )
    edit_response = client.put(f"/route-points/{point_id}", json=updated_data)
    assert edit_response.status_code == 200
    updated_point = edit_response.json()
    assert updated_point["point_name"] == updated_data["point_name"]
    assert updated_point["latitude"] == updated_data["latitude"]
    assert updated_point["longitude"] == updated_data["longitude"]


def test_list_stops_one_per_name(route_id):
    # The same stop on two routes must show once in the picker
    other = client.post("/routes/", json={"route_name": "Test Route 2"}).json()["id"]
    try:
        for rid in (route_id, other):
            client.post("/route-points/", json=point(rid, point_name="Zzq Search Stop"))

        response = client.get("/route-points/")

        assert response.status_code == 200
        assert [s["point_name"] for s in response.json()].count("Zzq Search Stop") == 1
    finally:
        client.delete(f"/routes/{other}")
