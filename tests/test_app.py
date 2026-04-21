"""
Tests for the Mergington High School Activities API using AAA pattern
(Arrange-Act-Assert)
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Arrange: Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        }
    }
    
    # Clear and restore
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Cleanup
    activities.clear()
    activities.update(original_activities)


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) >= len(expected_activities)
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_contains_required_fields(self, client, reset_activities):
        """Test that activity objects contain all required fields"""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # Assert
        for field in required_fields:
            assert field in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, client, reset_activities):
        """Test successful signup for an activity"""
        # Arrange
        activity_name = "Basketball Team"
        email = "newstudent@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "message" in response.json()
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count + 1
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Non-Existent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_registration_prevented(self, client, reset_activities):
        """Test that a student cannot register twice for the same activity"""
        # Arrange
        activity_name = "Programming Class"
        email = "duplicate@mergington.edu"
        
        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Act - Attempt duplicate signup
        response2 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
        # Verify only one instance exists
        assert activities[activity_name]["participants"].count(email) == 1
    
    def test_signup_existing_participant_cannot_signup_again(self, client, reset_activities):
        """Test that existing participants cannot sign up again"""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_email}"
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
        # Verify no duplicate was added
        assert len(activities[activity_name]["participants"]) == initial_count


class TestRemoveParticipant:
    """Tests for the DELETE /activities/{activity_name}/participants/{email} endpoint"""
    
    def test_remove_participant_successful(self, client, reset_activities):
        """Test successful removal of a participant"""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(activities[activity_name]["participants"])
        assert email in activities[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == initial_count - 1
    
    def test_remove_participant_activity_not_found(self, client, reset_activities):
        """Test removal from non-existent activity returns 404"""
        # Arrange
        nonexistent_activity = "Non-Existent Club"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/participants/{email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_remove_participant_not_registered(self, client, reset_activities):
        """Test removal of student not registered for activity returns 404"""
        # Arrange
        activity_name = "Chess Club"
        unregistered_email = "notaparticipant@mergington.edu"
        assert unregistered_email not in activities[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/participants/{unregistered_email}"
        )
        
        # Assert
        assert response.status_code == 404
        assert "not signed up" in response.json()["detail"]


class TestIntegrationWorkflows:
    """Integration tests for complex workflows"""
    
    def test_signup_remove_signup_workflow(self, client, reset_activities):
        """Test complete workflow: signup, remove, then signup again"""
        # Arrange
        activity_name = "Soccer Club"
        email = "integration@mergington.edu"
        
        # Act & Assert - First signup
        response1 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response1.status_code == 200
        assert email in activities[activity_name]["participants"]
        
        # Act & Assert - Remove
        response2 = client.delete(
            f"/activities/{activity_name}/participants/{email}"
        )
        assert response2.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Act & Assert - Signup again
        response3 = client.post(f"/activities/{activity_name}/signup?email={email}")
        assert response3.status_code == 200
        assert email in activities[activity_name]["participants"]
    
    def test_multiple_students_signup_same_activity(self, client, reset_activities):
        """Test multiple students successfully signing up for the same activity"""
        # Arrange
        activity_name = "Art Club"
        students = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        initial_count = len(activities[activity_name]["participants"])
        
        # Act
        responses = []
        for student in students:
            response = client.post(
                f"/activities/{activity_name}/signup?email={student}"
            )
            responses.append(response)
        
        # Assert
        for response in responses:
            assert response.status_code == 200
        
        for student in students:
            assert student in activities[activity_name]["participants"]
        
        assert len(activities[activity_name]["participants"]) == initial_count + len(students)
    
    def test_remove_and_re_add_participant(self, client, reset_activities):
        """Test that removing a participant preserves activity state correctly"""
        # Arrange
        activity_name = "Gym Class"
        email1 = "john@mergington.edu"  # Existing participant
        email2 = "new@mergington.edu"   # New participant
        
        # Act - Add new participant
        response1 = client.post(f"/activities/{activity_name}/signup?email={email2}")
        assert response1.status_code == 200
        
        # Act - Remove existing participant
        response2 = client.delete(
            f"/activities/{activity_name}/participants/{email1}"
        )
        assert response2.status_code == 200
        
        # Assert - Verify state
        assert email1 not in activities[activity_name]["participants"]
        assert email2 in activities[activity_name]["participants"]
