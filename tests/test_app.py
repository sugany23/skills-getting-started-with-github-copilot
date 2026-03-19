import pytest
import copy
from fastapi.testclient import TestClient
from src import app


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test to ensure test isolation"""
    # Arrange: Save original state
    original = copy.deepcopy(app.activities)
    
    yield
    
    # Cleanup: Restore original state
    app.activities.clear()
    app.activities.update(original)


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app.app)


def test_root_redirect(client):
    """Test that GET / redirects to the static index page"""
    # Arrange - no special setup needed
    
    # Act
    response = client.get("/")
    
    # Assert
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test retrieving all activities"""
    # Arrange - activities are already set up in the fixture
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) == 9  # Should have 9 activities
    assert "Chess Club" in data
    assert "Programming Class" in data
    
    # Check structure of one activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club
    assert isinstance(chess_club["participants"], list)


def test_signup_success(client):
    """Test successful signup for an activity"""
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"
    
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "Signed up" in result["message"]
    assert email in result["message"]
    
    # Verify the student was added
    response2 = client.get("/activities")
    data = response2.json()
    assert email in data[activity_name]["participants"]


def test_signup_activity_not_found(client):
    """Test signup for non-existent activity"""
    # Arrange
    invalid_activity = "NonExistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.post(f"/activities/{invalid_activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_signup_already_signed_up(client):
    """Test signup when student is already registered"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already in participants
    
    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    
    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "Student already signed up" in result["detail"]


def test_delete_success(client):
    """Test successful unregister from an activity"""
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"  # Already signed up
    
    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert "Unregistered" in result["message"]
    assert email in result["message"]
    
    # Verify the student was removed
    response2 = client.get("/activities")
    data = response2.json()
    assert email not in data[activity_name]["participants"]


def test_delete_activity_not_found(client):
    """Test delete from non-existent activity"""
    # Arrange
    invalid_activity = "NonExistent Club"
    email = "student@mergington.edu"
    
    # Act
    response = client.delete(f"/activities/{invalid_activity}/signup?email={email}")
    
    # Assert
    assert response.status_code == 404
    result = response.json()
    assert "Activity not found" in result["detail"]


def test_delete_not_signed_up(client):
    """Test delete when student is not registered"""
    # Arrange
    activity_name = "Chess Club"
    email = "notsignedup@mergington.edu"  # Not in participants
    
    # Act
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    
    # Assert
    assert response.status_code == 400
    result = response.json()
    assert "Student not signed up" in result["detail"]