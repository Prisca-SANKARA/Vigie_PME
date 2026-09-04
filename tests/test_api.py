import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import db.session as session_module
from db.models import Base
from fastapi.testclient import TestClient
from scanner.models import Finding, Severity
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture()
def client(monkeypatch, tmp_path):
    # Base SQLite isolée en fichier temporaire pour ne pas polluer scans.db.
    test_db_url = f"sqlite:///{tmp_path / 'test_scans.db'}"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    monkeypatch.setattr(session_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", TestSessionLocal)

    from api.main import app

    with TestClient(app) as test_client:
        yield test_client


def register_and_get_token(client, email="pme@example.test", password="motdepasse123") -> str:
    response = client.post(
        "/auth/register",
        json={"email": email, "password": password, "company_name": "PME Test"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_then_login(client):
    register_and_get_token(client, email="a@example.test")

    response = client.post(
        "/auth/login", data={"username": "a@example.test", "password": "motdepasse123"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_with_wrong_password_fails(client):
    register_and_get_token(client, email="b@example.test")

    response = client.post(
        "/auth/login", data={"username": "b@example.test", "password": "mauvais"}
    )
    assert response.status_code == 401


def test_duplicate_registration_rejected(client):
    register_and_get_token(client, email="c@example.test")

    response = client.post(
        "/auth/register",
        json={"email": "c@example.test", "password": "x", "company_name": "Autre"},
    )
    assert response.status_code == 400


def test_scan_requires_authentication(client):
    response = client.post("/scans", json={"target": "example.test"})
    assert response.status_code == 401


def test_create_scan_persists_and_returns_findings(client, monkeypatch):
    token = register_and_get_token(client)

    fake_findings = [
        Finding(
            category="ssl",
            severity=Severity.CRITICAL,
            title="Certificat expiré",
            detail="Test",
            recommendation="Renouveler",
        )
    ]
    monkeypatch.setattr(
        "api.main.perform_scan", lambda target: ("example.test", fake_findings)
    )

    response = client.post(
        "/scans", json={"target": "example.test"}, headers=auth_headers(token)
    )
    assert response.status_code == 200

    body = response.json()
    assert body["target"] == "example.test"
    assert body["score"] == 80
    assert len(body["findings"]) == 1
    assert body["findings"][0]["title"] == "Certificat expiré"


def test_scans_are_isolated_between_clients(client, monkeypatch):
    monkeypatch.setattr("api.main.perform_scan", lambda target: (target, []))

    token_a = register_and_get_token(client, email="clienta@example.test")
    token_b = register_and_get_token(client, email="clientb@example.test")

    client.post("/scans", json={"target": "a.test"}, headers=auth_headers(token_a))
    client.post("/scans", json={"target": "a.test"}, headers=auth_headers(token_b))

    response_a = client.get("/scans/a.test", headers=auth_headers(token_a))
    response_b = client.get("/scans/a.test", headers=auth_headers(token_b))

    assert len(response_a.json()) == 1
    assert len(response_b.json()) == 1


def test_get_scan_detail_of_another_client_returns_404(client, monkeypatch):
    monkeypatch.setattr("api.main.perform_scan", lambda target: (target, []))

    token_a = register_and_get_token(client, email="owner@example.test")
    token_b = register_and_get_token(client, email="stranger@example.test")

    created = client.post(
        "/scans", json={"target": "private.test"}, headers=auth_headers(token_a)
    ).json()

    response = client.get(
        f"/scans/detail/{created['id']}", headers=auth_headers(token_b)
    )
    assert response.status_code == 404


def test_get_scan_detail_not_found_returns_404(client):
    token = register_and_get_token(client)
    response = client.get("/scans/detail/999", headers=auth_headers(token))
    assert response.status_code == 404
