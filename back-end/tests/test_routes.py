
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

NON_EXISTENT_ID = "00000000-0000-0000-0000-000000000001"


def test_create_missing_name():
    response = client.post("/routes/", json={"route_name": ""})
    assert response.status_code == 422


def test_edit_route_missing_name():
    response = client.put(
        f"/routes/{NON_EXISTENT_ID}",
        json={"route_name": ""}
    )
    assert response.status_code == 422


def test_delete_route_missing_id():
    response = client.delete("/routes/")
    assert response.status_code == 405


def test_update_route_id_not_found():
    response = client.put(
        f"/routes/{NON_EXISTENT_ID}",
        json={"route_name": "Updated Route"}
    )
    assert response.status_code == 404


def test_delete_route_id_not_found():
    response = client.delete(f"/routes/{NON_EXISTENT_ID}")
    assert response.status_code == 404


def test_update_route_missing_id():
    response = client.put("/routes/", json={"route_name": "Updated Route", "updated_at":""})
    assert response.status_code == 405


def test_delete_route_invalid_id():
    response = client.delete("/routes/invalid_route_id")
    assert response.status_code == 422


def test_update_route_invalid_id():
    response = client.put(
        "/routes/invalid_route_id",
        json={"route_name": "Updated Route"}
    )
    assert response.status_code == 422


def test_create_route():
    route_data = {
        "route_name": "Test Route"
    }

    response = client.post("/routes/", json=route_data)

    assert response.status_code == 201

    response_data = response.json()

    assert response_data["route_name"] == route_data["route_name"]
