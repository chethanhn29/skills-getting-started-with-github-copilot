"""
Pytest tests for the Mergington High School API using AAA pattern.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def reset_activities():
    original = {
        key: {
            "description": act["description"],
            "schedule": act["schedule"],
            "max_participants": act["max_participants"],
            "participants": act["participants"].copy(),
        }
        for key, act in activities.items()
    }
    yield
    for key in activities:
        activities[key]["participants"] = original[key]["participants"].copy()


class TestRootEndpoint:
    def test_root_redirect_returns_307(self, client):
        # Arrange
        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Art Club" in data


class TestSignupEndpoint:
    def test_signup_success_adds_participant(self, client, reset_activities):
        # Arrange
        activity_name = "Art Club"
        email = "newstudent@mergington.edu"
        starting_count = len(activities[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == starting_count + 1

    def test_signup_activity_not_found(self, client, reset_activities):
        # Arrange
        # Act
        response = client.post(
            "/activities/NonExistent/signup",
            params={"email": "student@mergington.edu"},
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_invalid_email_format(self, client, reset_activities):
        # Arrange
        # Act & Assert
        for bad_email in ["invalidemail", "invalid@email"]:
            response = client.post(
                "/activities/Art Club/signup",
                params={"email": bad_email},
            )
            assert response.status_code == 400
            assert response.json()["detail"] == "Invalid email format"

    def test_signup_student_already_signed_up(self, client, reset_activities):
        # Arrange
        email = "michael@mergington.edu"

        # Act
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"


class TestUnregisterEndpoint:
    def test_unregister_success_removes_participant(self, client, reset_activities):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        starting_count = len(activities[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == starting_count - 1

    def test_unregister_student_not_signed_up(self, client, reset_activities):
        # Arrange
        email = "notstudent@mergington.edu"

        # Act
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email},
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"
