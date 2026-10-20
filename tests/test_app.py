from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def preserve_activity_state():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Soccer Club"]["description"]
    assert response.json()["Soccer Club"]["participants"] == []


def test_signup_adds_participant(client):
    email = "student@example.com"
    activity_path = quote("Soccer Club", safe="")

    response = client.post(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Soccer Club"}
    assert email in client.get("/activities").json()["Soccer Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    activity_path = quote("Soccer Club", safe="")
    params = {"email": "student@example.com"}
    client.post(f"/activities/{activity_path}/signup", params=params)

    response = client.post(f"/activities/{activity_path}/signup", params=params)

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"
    assert client.get("/activities").json()["Soccer Club"]["participants"] == [
        "student@example.com"
    ]


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        f"/activities/{quote('Unknown Activity', safe='')}/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(client):
    activity_path = quote("Soccer Club", safe="")
    email = "student@example.com"
    client.post(f"/activities/{activity_path}/signup", params={"email": email})

    response = client.delete(
        f"/activities/{activity_path}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Soccer Club"}
    assert email not in client.get("/activities").json()["Soccer Club"]["participants"]


def test_unregister_rejects_unknown_activity(client):
    response = client.delete(
        f"/activities/{quote('Unknown Activity', safe='')}/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_rejects_unregistered_participant(client):
    response = client.delete(
        f"/activities/{quote('Soccer Club', safe='')}/signup",
        params={"email": "student@example.com"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"