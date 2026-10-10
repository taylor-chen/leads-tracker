from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select

from app.models import RevokedToken
from tests.conftest import ATTORNEY_EMAIL, ATTORNEY_PASSWORD


def test_login_and_me(client, attorney):
    res = client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL.upper(), "password": ATTORNEY_PASSWORD}
    )
    assert res.status_code == 200
    token = res.json()
    assert token["token_type"] == "bearer"
    assert token["expires_in"] > 0

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == ATTORNEY_EMAIL


def test_login_wrong_password(client, attorney):
    res = client.post("/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["error"]["message"] == "Invalid email or password"


def test_login_unknown_user(client):
    res = client.post("/api/v1/auth/login", json={"email": "who@x.com", "password": "whatever1"})
    assert res.status_code == 401


def test_inactive_user_cannot_login(client, attorney, db):
    attorney.is_active = False
    db.add(attorney)
    db.commit()
    res = client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert res.status_code == 401


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def _login(client) -> dict[str, str]:
    res = client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert res.status_code == 200
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_logout_revokes_token(client, auth_headers):
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 200

    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 204

    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401
    assert client.get("/api/v1/leads", headers=auth_headers).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 401


def test_logout_only_revokes_that_session(client, attorney):
    laptop, phone = _login(client), _login(client)
    assert client.post("/api/v1/auth/logout", headers=laptop).status_code == 204
    assert client.get("/api/v1/auth/me", headers=laptop).status_code == 401
    assert client.get("/api/v1/auth/me", headers=phone).status_code == 200


def test_logout_requires_token(client):
    assert client.post("/api/v1/auth/logout").status_code == 401
    bad = {"Authorization": "Bearer not-a-jwt"}
    assert client.post("/api/v1/auth/logout", headers=bad).status_code == 401


def test_token_without_jti_is_rejected(client, attorney, settings):
    token = jwt.encode(
        {"sub": str(attorney.id), "exp": datetime.now(UTC) + timedelta(minutes=5)},
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    res = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401


def test_logout_prunes_expired_revocations(client, attorney, db):
    db.add(RevokedToken(jti="old", expires_at=datetime.now(UTC) - timedelta(minutes=1)))
    db.commit()

    assert client.post("/api/v1/auth/logout", headers=_login(client)).status_code == 204

    db.expire_all()
    remaining = db.scalars(select(RevokedToken.jti)).all()
    assert "old" not in remaining
    assert len(remaining) == 1
