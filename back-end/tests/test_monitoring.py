from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.db.database import SessionLocal
from app.main import app
from app.monitoring.model import AdminAuditLog, FareLookup
from tests.conftest import ADMIN_HEADERS

client = TestClient(app, headers=ADMIN_HEADERS)
anonymous = TestClient(app)


def test_security_headers_on_every_response():
    headers = anonymous.get("/health").headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["content-security-policy"] == "default-src 'none'; frame-ancestors 'none'"
    assert "max-age" in headers["strict-transport-security"]
    # Swagger UI loads its scripts from a CDN, so the docs page has no CSP
    assert "content-security-policy" not in anonymous.get("/docs").headers


def test_monitoring_needs_an_admin():
    assert anonymous.get("/v1/admin/stats").status_code == 401
    assert anonymous.get("/v1/admin/audit-log").status_code == 401


def test_lookups_are_logged_and_counted():
    a, b = (client.post("/v1/admin/stops", json={"name": f"Monitor {n}", "latitude": 14.65, "longitude": 121.1}).json()["id"]
            for n in "AB")
    try:
        before = client.get("/v1/admin/stats").json()
        # No route connects the two new stops: an unsupported trip
        params = {"origin_stop_id": a, "destination_stop_id": b, "puv_type": "traditional_jeepney"}
        assert anonymous.get("/v1/fares/estimate", params=params).status_code == 200

        with SessionLocal() as db:
            lookup = db.execute(select(FareLookup).where(FareLookup.origin_stop_id == a)).scalar_one()
        assert (lookup.route_count, lookup.has_fare) == (0, False)
        assert lookup.duration_ms >= 0

        after = client.get("/v1/admin/stats").json()
        assert after["total_lookups"] == before["total_lookups"] + 1
        assert after["daily"][-1]["lookups"] >= 1
        assert 0 < after["unsupported_rate"] <= 1
        assert {"puv_type", "age_days"} <= set(after["fare_data"][0])
    finally:
        for stop_id in (a, b):  # cascades to the lookup
            client.delete(f"/v1/admin/stops/{stop_id}")


def test_admin_changes_are_audited_and_reads_are_not():
    with SessionLocal() as db:
        db.execute(delete(AdminAuditLog).where(AdminAuditLog.admin_email == "admin@test.local"))
        db.commit()

    client.get("/v1/admin/audit-log")
    stop_id = client.post("/v1/admin/stops", json={"name": "Audit Stop", "latitude": 14.65, "longitude": 121.1}).json()["id"]
    client.delete(f"/v1/admin/stops/{stop_id}")

    entries = [e for e in client.get("/v1/admin/audit-log").json() if e["admin_email"] == "admin@test.local"]
    assert [(e["method"], e["status_code"]) for e in entries] == [("DELETE", 204), ("POST", 201)]
    assert entries[0]["path"] == f"/v1/admin/stops/{stop_id}"
