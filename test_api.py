import os
import tempfile

_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_db.close()
os.environ["DATABASE_URL"] = "sqlite:///" + _db.name
os.environ["JWT_SECRET"] = "test-secret-that-is-long-enough-for-testing-only"
os.environ["UPSTREAM_URL"] = "http://127.0.0.1:9/v1"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_auth_required_for_scan():
    response = client.post("/scan", files={"f": ("x.txt", b"hello", "text/plain")})
    assert response.status_code == 401


def test_initial_admin_bootstrap_and_registration_closes():
    response = client.post("/auth/register", json={"email": "admin-test@example.com", "password": "correct-horse-battery-9"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"
    second = client.post("/auth/register", json={"email": "other-test@example.com", "password": "correct-horse-battery-10"})
    assert second.status_code == 403


def test_login_and_document_listing():
    login = client.post("/auth/login", json={"email": "admin-test@example.com", "password": "correct-horse-battery-9"})
    assert login.status_code == 200
    token = login.json()["token"]
    response = client.get("/documents", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
