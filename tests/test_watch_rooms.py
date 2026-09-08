from tests.test_flow import identity_headers


def test_watch_room_uses_authenticated_identity_and_permissions(client):
    host_headers = identity_headers(username="ana", email="ana@example.com")
    guest_headers = identity_headers(username="carlos", email="carlos@example.com")
    created = client.post("/api/v1/watch-rooms", headers=host_headers, json={
        "movieId": "550e8400-e29b-41d4-a716-446655440000",
    })
    assert created.status_code == 201
    room = created.json()
    assert client.post("/api/v1/watch-rooms", headers=host_headers, json={
        "movieId": "550e8400-e29b-41d4-a716-446655440000", "hostUserId": 999,
    }).status_code == 422
    joined = client.post(
        f"/api/v1/watch-rooms/{room['code']}/join", headers=guest_headers,
        json={"nickname": "Carlos"},
    )
    assert joined.status_code == 200
    fetched = client.get(f"/api/v1/watch-rooms/{room['code']}")
    participants = fetched.json()["participants"]
    guest_id = next(item["userId"] for item in participants if item["role"] == "VIEWER")
    assert client.delete(
        f"/api/v1/watch-rooms/{room['code']}/participants/{guest_id}", headers=host_headers
    ).status_code == 204
