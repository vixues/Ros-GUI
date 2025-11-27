"""Tests for drone management."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.server import app
from backend.models.user import User
from backend.models.drone import Drone


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def auth_token(client: TestClient, test_user: User) -> str:
    """Get authentication token."""
    response = client.post(
        "/api/auth/login",
        data={
            "username": "testuser",
            "password": "testpassword"
        }
    )
    return response.json()["data"]["access_token"]


@pytest.mark.asyncio
async def test_create_drone(client: TestClient, auth_token: str):
    """Test creating a drone."""
    response = client.post(
        "/api/drones",
        json={
            "name": "Test Drone",
            "drone_id": "drone_001",
            "connection_url": "ws://localhost:9090"
        },
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == 201
    assert data["data"]["name"] == "Test Drone"
    assert data["data"]["drone_id"] == "drone_001"


@pytest.mark.asyncio
async def test_get_drones(client: TestClient, auth_token: str, db_session: AsyncSession):
    """Test getting list of drones."""
    # Create a test drone
    drone = Drone(
        name="Test Drone",
        drone_id="drone_001",
        status="idle"
    )
    db_session.add(drone)
    await db_session.commit()
    
    response = client.get(
        "/api/drones",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_drone_by_id(client: TestClient, auth_token: str, db_session: AsyncSession):
    """Test getting drone by ID."""
    # Create a test drone
    drone = Drone(
        name="Test Drone",
        drone_id="drone_001",
        status="idle"
    )
    db_session.add(drone)
    await db_session.commit()
    await db_session.refresh(drone)
    
    response = client.get(
        f"/api/drones/{drone.id}",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == 200
    assert data["data"]["id"] == drone.id
    assert data["data"]["name"] == "Test Drone"


@pytest.mark.asyncio
async def test_get_drone_not_found(client: TestClient, auth_token: str):
    """Test getting non-existent drone."""
    response = client.get(
        "/api/drones/99999",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 404

