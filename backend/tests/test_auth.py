from datetime import UTC, datetime, timedelta

import jwt
from sqlalchemy import select

from app.models import RevokedToken
from tests.conftest import ATTORNEY_EMAIL, ATTORNEY_PASSWORD, login_headers


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


def test_logout_revokes_token(client, auth_headers):
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 200

    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 204

    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 401
    assert client.get("/api/v1/leads", headers=auth_headers).status_code == 401
    assert client.post("/api/v1/auth/logout", headers=auth_headers).status_code == 401


def test_logout_only_revokes_that_session(client, attorney):
    laptop, phone = login_headers(client), login_headers(client)
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

    assert client.post("/api/v1/auth/logout", headers=login_headers(client)).status_code == 204

    db.expire_all()
    remaining = db.scalars(select(RevokedToken.jti)).all()
    assert "old" not in remaining
    assert len(remaining) == 1


NEW_PASSWORD = "n3w-s3cret-password"


def _change_password(client, headers, current=ATTORNEY_PASSWORD, new=NEW_PASSWORD):
    return client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={"current_password": current, "new_password": new},
    )


def test_change_password(client, auth_headers):
    assert _change_password(client, auth_headers).status_code == 204

    old = client.post(
        "/api/v1/auth/login", json={"email": ATTORNEY_EMAIL, "password": ATTORNEY_PASSWORD}
    )
    assert old.status_code == 401
    headers = login_headers(client, password=NEW_PASSWORD)
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 200


def test_change_password_invalidates_existing_tokens(client, attorney):
    laptop, phone = login_headers(client), login_headers(client)

    assert _change_password(client, laptop).status_code == 204

    for headers in (laptop, phone):
        assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
        assert client.get("/api/v1/leads", headers=headers).status_code == 401


def test_change_password_wrong_current_password(client, auth_headers):
    res = _change_password(client, auth_headers, current="not-my-password")
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "invalid_current_password"
    # Nothing changed: the session and the old password still work.
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 200
    assert login_headers(client)


def test_change_password_requires_auth(client, attorney):
    res = _change_password(client, {})
    assert res.status_code == 401
    assert res.json()["error"]["code"] == "not_authenticated"


def test_change_password_policy(client, auth_headers):
    for new, message in [
        ("short", "Password must be at least 8 characters"),
        ("x" * 73, "Password must be at most 72 bytes"),
        (ATTORNEY_PASSWORD, "New password must be different from the current password"),
    ]:
        res = _change_password(client, auth_headers, new=new)
        assert res.status_code == 422, new
        assert res.json()["error"]["message"] == message
    assert client.get("/api/v1/auth/me", headers=auth_headers).status_code == 200


def test_token_with_stale_version_is_rejected(client, attorney, settings):
    def token(ver):
        payload = {
            "sub": str(attorney.id),
            "jti": f"jti-{ver}",
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        }
        if ver is not None:
            payload["ver"] = ver
        encoded = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
        return {"Authorization": f"Bearer {encoded}"}

    # Tokens issued before the `ver` claim existed are treated as version 0.
    assert client.get("/api/v1/auth/me", headers=token(None)).status_code == 200
    assert client.get("/api/v1/auth/me", headers=token(0)).status_code == 200
    assert client.get("/api/v1/auth/me", headers=token(1)).status_code == 401
    assert client.get("/api/v1/auth/me", headers=token("0")).status_code == 401

    assert _change_password(client, token(0)).status_code == 204
    assert client.get("/api/v1/auth/me", headers=token(None)).status_code == 401
    assert client.get("/api/v1/auth/me", headers=token(1)).status_code == 200
