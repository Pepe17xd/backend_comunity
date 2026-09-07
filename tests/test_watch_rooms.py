from tests.test_flow import login, register


def test_watch_room_lifecycle(client):
    register(client)
    register(client, "carlos", "carlos@example.com", "secret123")

    created = client.post("/api/v1/watch-rooms", json={
        "movieId": "550e8400-e29b-41d4-a716-446655440000",
        "hostUserId": 1,
    })
    assert created.status_code == 201
    room = created.json()
    assert room["status"] == "WAITING"
    assert room["movieId"] == "550e8400-e29b-41d4-a716-446655440000"

    joined = client.post(f"/api/v1/watch-rooms/{room['code']}/join", json={"userId": 2, "nickname": "Carlos"})
    assert joined.status_code == 200
    assert joined.json() == {"roomId": room["id"], "joined": True}

    fetched = client.get(f"/api/v1/watch-rooms/{room['code']}")
    assert fetched.status_code == 200
    assert {participant["role"] for participant in fetched.json()["participants"]} == {"HOST", "VIEWER"}

    duplicate = client.post(f"/api/v1/watch-rooms/{room['code']}/join", json={"userId": 2, "nickname": "Carlos"})
    assert duplicate.status_code == 409
