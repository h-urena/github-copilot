import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

def test_get_activities():
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()

    # Check that we have activities
    assert isinstance(data, dict)
    assert len(data) > 0

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)

def test_signup_for_activity():
    """Test signing up for an activity"""
    # Use an activity that exists
    activity_name = "Basketball Team"  # This one starts with no participants

    # Sign up a student
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "test@student.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Signed up" in data["message"]

    # Check that the student was added
    response = client.get("/activities")
    activities = response.json()
    assert "test@student.edu" in activities[activity_name]["participants"]

def test_signup_duplicate():
    """Test signing up for the same activity twice"""
    activity_name = "Basketball Team"

    # Try to sign up the same student again
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "test@student.edu"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "already signed up" in data["detail"].lower()

def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity"""
    response = client.post(
        "/activities/NonExistent/signup",
        params={"email": "test@student.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_unregister_from_activity():
    """Test unregistering from an activity"""
    activity_name = "Basketball Team"

    # First sign up
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "unregister@test.edu"}
    )

    # Then unregister
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": "unregister@test.edu"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Unregistered" in data["message"]

    # Check that the student was removed
    response = client.get("/activities")
    activities = response.json()
    assert "unregister@test.edu" not in activities[activity_name]["participants"]

def test_unregister_not_signed_up():
    """Test unregistering a student who isn't signed up"""
    activity_name = "Basketball Team"

    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": "notsignedup@test.edu"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "not signed up" in data["detail"].lower()

def test_unregister_nonexistent_activity():
    """Test unregistering from a non-existent activity"""
    response = client.delete(
        "/activities/NonExistent/unregister",
        params={"email": "test@student.edu"}
    )
    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()

def test_root_redirect():
    """Test that root redirects to static HTML"""
    # Create a client that doesn't follow redirects
    client_no_redirect = TestClient(app, follow_redirects=False)
    response = client_no_redirect.get("/")
    assert response.status_code == 307  # Temporary redirect
    assert "/static/index.html" in response.headers["location"]

def test_activity_capacity_limit():
    """Test that signup fails when activity reaches max capacity"""
    # Use an activity with low capacity
    activity_name = "Chess Club"  # Has max_participants: 12, but already has 2 participants

    # Fill up the remaining spots (12 - 2 = 10 spots left)
    for i in range(10):
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": f"student{i}@test.edu"}
        )
        assert response.status_code == 200

    # Try to sign up one more (should fail)
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@test.edu"}
    )
    assert response.status_code == 400
    data = response.json()
    assert "capacity" in data["detail"].lower() or "full" in data["detail"].lower()

def test_static_files_served():
    """Test that static files are served correctly"""
    # Test HTML file
    response = client.get("/static/index.html")
    assert response.status_code == 200
    assert "Mergington High School" in response.text
    assert "Extracurricular Activities" in response.text

    # Test CSS file
    response = client.get("/static/styles.css")
    assert response.status_code == 200
    assert "box-sizing" in response.text

    # Test JS file
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "DOMContentLoaded" in response.text

def test_signup_empty_email():
    """Test signup with empty email"""
    activity_name = "Basketball Team"
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": ""}
    )
    # This should either fail validation or succeed depending on implementation
    # For now, just check it doesn't crash
    assert response.status_code in [200, 400]