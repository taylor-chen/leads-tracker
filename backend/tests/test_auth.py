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
