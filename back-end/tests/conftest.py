import os

# Set before the app is imported: the admin key for write tests, and a rate limit the suite never hits
os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
os.environ.setdefault("PUBLIC_RATE_LIMIT_PER_MINUTE", "100000")

ADMIN_HEADERS = {"X-Admin-Key": os.environ["ADMIN_API_KEY"]}

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.db.database import get_db
from app.main import app


@pytest.fixture
def client():
    mock_db = MagicMock()

    def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()