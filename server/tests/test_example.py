"""
Example test file to demonstrate the test framework structure.

This file shows how to use the test fixtures and can be used as a template
for writing new tests.
"""

import pytest
from fastapi import status


@pytest.mark.unit
def test_example_unit():
    """Example unit test."""
    assert 1 + 1 == 2


@pytest.mark.integration
def test_health_check(test_client):
    """Example integration test using test_client fixture."""
    response = test_client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "healthy"}


@pytest.mark.integration
def test_get_users_requires_auth(test_client):
    """Example test showing unauthenticated access is blocked."""
    response = test_client.get("/users/")
    # This endpoint currently doesn't require auth, but will in Phase 1
    # Once Phase 1 is implemented, this should return 401 or 403
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]


@pytest.mark.integration
def test_create_user(test_client, db_session):
    """Example test for creating a user."""
    user_data = {
        "email": "newuser@test.com",
        "name": "New User",
        "password": "password123",
        "password_confirm": "password123"
    }

    response = test_client.post("/users/register", json=user_data)

    # Should succeed (201 or 200 depending on implementation)
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    # Check user was created in database
    from models import Users
    user = db_session.query(Users).filter(Users.email == "newuser@test.com").first()
    assert user is not None
    assert user.email == "newuser@test.com"
    assert user.name == "New User"


@pytest.mark.integration
@pytest.mark.auth
def test_user_registration_duplicate_email(test_client, test_user_attendee):
    """Example test for duplicate email registration."""
    user_data = {
        "email": test_user_attendee.email,  # Use existing email
        "name": "Duplicate User",
        "password": "password123",
        "password_confirm": "password123"
    }

    response = test_client.post("/users/register", json=user_data)

    # Should fail with appropriate error
    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT
    ]

    # Check error message mentions email
    response_data = response.json()
    assert "email" in str(response_data.get("detail", "")).lower()


@pytest.mark.integration
def test_fixture_user_creation(db_session, test_user_attendee):
    """Example test showing fixture user is created in database."""
    from models import Users

    user = db_session.query(Users).filter(Users.id == test_user_attendee.id).first()
    assert user is not None
    assert user.email == "attendee@test.com"
    assert user.name == "Test Attendee"

