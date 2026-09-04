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


def _extract_token_from_reset_link(reset_link: str) -> str:
    from urllib.parse import parse_qs, urlparse

    return parse_qs(urlparse(reset_link).query)["token"][0]


def test_forgot_password_returns_same_generic_message_whether_or_not_account_exists(
    client, monkeypatch
):
    monkeypatch.setattr("api.main.send_password_reset_email", lambda email, link: None)
    register_and_get_token(client, email="known@example.test")

    known = client.post("/auth/forgot-password", json={"email": "known@example.test"})
    unknown = client.post("/auth/forgot-password", json={"email": "unknown@example.test"})

    assert known.status_code == 200
    assert unknown.status_code == 200
    assert known.json() == unknown.json()


def test_full_reset_password_flow_allows_login_with_new_password(client, monkeypatch):
    captured = {}

    def fake_send(email, reset_link):
        captured["link"] = reset_link

    monkeypatch.setattr("api.main.send_password_reset_email", fake_send)
    register_and_get_token(client, email="reset@example.test", password="ancienmdp123")

    client.post("/auth/forgot-password", json={"email": "reset@example.test"})
    reset_token = _extract_token_from_reset_link(captured["link"])

    response = client.post(
        "/auth/reset-password",
        json={"token": reset_token, "new_password": "nouveaumdp456"},
    )
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login", data={"username": "reset@example.test", "password": "ancienmdp123"}
    )
    new_login = client.post(
        "/auth/login", data={"username": "reset@example.test", "password": "nouveaumdp456"}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_reset_token_cannot_be_reused(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "api.main.send_password_reset_email",
        lambda email, link: captured.update(link=link),
    )
    register_and_get_token(client, email="reuse@example.test")

    client.post("/auth/forgot-password", json={"email": "reuse@example.test"})
    reset_token = _extract_token_from_reset_link(captured["link"])

    first = client.post(
        "/auth/reset-password", json={"token": reset_token, "new_password": "premierchange1"}
    )
    second = client.post(
        "/auth/reset-password", json={"token": reset_token, "new_password": "deuxiemechange2"}
    )
    assert first.status_code == 200
    assert second.status_code == 400


def test_reset_password_with_unknown_token_fails(client):
    response = client.post(
        "/auth/reset-password", json={"token": "token-inexistant", "new_password": "abcdefgh"}
    )
    assert response.status_code == 400


def test_reset_password_rejects_short_password(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(
        "api.main.send_password_reset_email",
        lambda email, link: captured.update(link=link),
    )
    register_and_get_token(client, email="short@example.test")

    client.post("/auth/forgot-password", json={"email": "short@example.test"})
    reset_token = _extract_token_from_reset_link(captured["link"])

    response = client.post(
        "/auth/reset-password", json={"token": reset_token, "new_password": "court"}
    )
    assert response.status_code == 400


def test_reset_password_with_expired_token_fails(client):
    from datetime import datetime, timedelta, timezone

    from db.models import Client, PasswordResetToken
    from db.session import SessionLocal

    register_and_get_token(client, email="expired@example.test")

    db = SessionLocal()
    try:
        owner = db.query(Client).filter(Client.email == "expired@example.test").first()
        expired_token = PasswordResetToken(
            client_id=owner.id,
            token="expired-token-123",
            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        )
        db.add(expired_token)
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/auth/reset-password",
        json={"token": "expired-token-123", "new_password": "nouveaumdp789"},
    )
    assert response.status_code == 400


def test_change_password_requires_authentication(client):
    response = client.post(
        "/auth/change-password",
        json={"current_password": "x", "new_password": "nouveaumdp123"},
    )
    assert response.status_code == 401


def test_change_password_success_allows_login_with_new_password(client):
    token = register_and_get_token(
        client, email="changepw@example.test", password="ancienmdp123"
    )

    response = client.post(
        "/auth/change-password",
        json={"current_password": "ancienmdp123", "new_password": "nouveaumdp999"},
        headers=auth_headers(token),
    )
    assert response.status_code == 200

    old_login = client.post(
        "/auth/login", data={"username": "changepw@example.test", "password": "ancienmdp123"}
    )
    new_login = client.post(
        "/auth/login", data={"username": "changepw@example.test", "password": "nouveaumdp999"}
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200


def test_change_password_rejects_wrong_current_password(client):
    token = register_and_get_token(client, email="wrongcurrent@example.test")

    response = client.post(
        "/auth/change-password",
        json={"current_password": "mauvais", "new_password": "nouveaumdp123"},
        headers=auth_headers(token),
    )
    assert response.status_code == 401


def test_change_password_rejects_short_new_password(client):
    token = register_and_get_token(
        client, email="shortnew@example.test", password="motdepasse123"
    )

    response = client.post(
        "/auth/change-password",
        json={"current_password": "motdepasse123", "new_password": "court"},
        headers=auth_headers(token),
    )
    assert response.status_code == 400
