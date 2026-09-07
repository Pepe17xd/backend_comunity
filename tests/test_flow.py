def register(client, username="ana", email="ana@example.com", password="secret123"):
    return client.post(
        "/api/v1/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "display_name": "Ana",
        },
    )


def login(client, username="ana", password="secret123"):
    return client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password},
    )


def test_register_login_create_club_and_join(client):
    r = register(client)
    assert r.status_code == 201

    r = login(client)
    assert r.status_code == 200
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post(
        "/api/v1/clubs",
        headers=headers,
        json={
            "name": "Cinefilos",
            "description": "Club para hablar de cine",
            "visibility": "PUBLIC",
        },
    )
    assert r.status_code == 201
    club_id = r.json()["id"]

    r = client.get(f"/api/v1/clubs/{club_id}/members")
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["role"] == "OWNER"

    register(client, "luis", "luis@example.com", "secret123")
    login_response = login(client, "luis", "secret123")
    luis_headers = {
        "Authorization": f"Bearer {login_response.json()['access_token']}"
    }

    r = client.post(
        f"/api/v1/clubs/{club_id}/members",
        headers=luis_headers,
    )
    assert r.status_code == 201
    assert r.json()["role"] == "MEMBER"
