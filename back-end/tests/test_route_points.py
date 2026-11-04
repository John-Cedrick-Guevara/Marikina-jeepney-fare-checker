from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

NON_EXISTENT_ID = "00000000-0000-0000-0000-000000000001"


def test_edit_route_point_missing_fields():
    response = client.put(
        f"/route_points/{NON_EXISTENT_ID}",
        json={}
    )
    assert response.status_code == 422

def test_delete_route_point_missing_id():
    response = client.delete("/route_points/")
    assert response.status_code == 405

def test_update_route_point_id_not_found():
    response = client.put(
        f"/route_points/{NON_EXISTENT_ID}",
        json={"point_name": "Updated Point"}
    )
    assert response.status_code == 404

def test_delete_route_point_id_not_found():
    response = client.delete(f"/route_points/{NON_EXISTENT_ID}")
    assert response.status_code == 404

def test_update_route_point_missing_id():
    response = client.put("/route_points/", json={"point_name": "Updated Point"})
    assert response.status_code == 405

def test_delete_route_point_invalid_id():
    response = client.delete("/route_points/invalid_point_id")
    assert response.status_code == 422

def test_update_route_point_invalid_id():
    response = client.put(
        "/route_points/invalid_point_id",
        json={"point_name": "Updated Point"}
    )
    assert response.status_code == 422

def test_create_route_point():
    point_data = {
        "point_name": "Test Point",
        "latitude": 12.345678,
        "longitude": 98.765432
    }
    response = client.post("/route_points/", json=point_data)
    assert response.status_code == 201
    data = response.json()
    assert data["point_name"] == point_data["point_name"]
    assert data["latitude"] == point_data["latitude"]
    assert data["longitude"] == point_data["longitude"]

def test_create_route_point_missing_fields():
    response = client.post("/route_points/", json={})
    assert response.status_code == 422

def test_create_route_point_invalid_latitude():
    point_data = {
        "point_name": "Test Point",
        "latitude": 200.0,  # Invalid latitude
        "longitude": 98.765432
    }
    response = client.post("/route_points/", json=point_data)
    assert response.status_code == 422

def test_create_route_point_invalid_longitude():
    point_data = {
        "point_name": "Test Point",
        "latitude": 12.345678,
        "longitude": 200.0  # Invalid longitude
    }
    response = client.post("/route_points/", json=point_data)
    assert response.status_code == 422

def test_edit_route_point():
    # First, create a route point to edit
    point_data = {
        "point_name": "Original Point",
        "latitude": 12.345678,
        "longitude": 98.765432
    }
    create_response = client.post("/route_points/", json=point_data)
    assert create_response.status_code == 201
    created_point = create_response.json()
    point_id = created_point["id"]

    # Now, edit the route point
    updated_data = {
        "point_name": "Updated Point",
        "latitude": 23.456789,
        "longitude": 87.654321
    }
    edit_response = client.put(f"/route_points/{point_id}", json=updated_data)
    assert edit_response.status_code == 200
    updated_point = edit_response.json()
    assert updated_point["point_name"] == updated_data["point_name"]
    assert updated_point["latitude"] == updated_data["latitude"]
    assert updated_point["longitude"] == updated_data["longitude"]