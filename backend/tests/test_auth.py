"""Tests for authentication."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.server import app
from backend.models.user import User
from backend.auth import get_password_hash


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_register_user(client: TestClient, db_session: AsyncSession):
    """Test user registration."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "full_name": "New User"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == 201
    assert data["message"] == "User registered successfully"
    assert data["data"]["username"] == "newuser"
    assert data["data"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: TestClient, test_user: User):
    """Test registration with duplicate username."""
    response = client.post(
        "/api/auth/register",
        json={
            "username": "testuser",
            "email": "different@example.com",
            "password": "password123"
        }
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_success(client: TestClient, test_user: User):
    """Test successful login."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: TestClient, test_user: User):
    """Test login with invalid credentials."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "wrongpassword"
        }
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: TestClient, test_user: User):
    """Test getting current user info."""
    # First login to get token
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    token = login_response.json()["data"]["access_token"]
    
    # Get current user
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["data"]["username"] == "testuser"

