from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt


def identity_headers(subject=None, username="ana", email="ana@example.com", **extra):
    payload = {
        "sub": str(subject or uuid4()), "username": username, "email": email,
        "iss": "identity-service", "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        **extra,
    }
    return {"Authorization": f"Bearer {jwt.encode(payload, 'test-secret', algorithm='HS256')}"}


def test_identity_token_provisions_profile_and_creates_club(client):
    headers = identity_headers()
    me = client.get("/api/v1/users/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["identity_user_id"]

    club = client.post("/api/v1/clubs", headers=headers, json={
        "name": "Cinefilos", "description": "Club para hablar de cine", "visibility": "PUBLIC",
    })
    assert club.status_code == 201
    members = client.get(f"/api/v1/clubs/{club.json()['id']}/members")
    assert members.status_code == 200
    assert members.json()[0]["role"] == "OWNER"


def test_rejects_invalid_issuer_and_expired_token(client):
    wrong_issuer = identity_headers(iss="other-service")
    assert client.get("/api/v1/users/me", headers=wrong_issuer).status_code == 401
    expired = identity_headers(exp=datetime.now(timezone.utc) - timedelta(seconds=1))
    assert client.get("/api/v1/users/me", headers=expired).status_code == 401
