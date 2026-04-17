import pytest
from app.models.user import User, UserRole
from app.core.security import get_password_hash

def test_admin_can_access_admin_panel(client, db, admin_token):
    # Setup: Create an admin user
    admin = User(
        email="admin@solshare.com",
        hashed_password=get_password_hash("admin1234"),
        full_name="System Administrator",
        role=UserRole.ADMIN
    )
    db.add(admin)
    db.commit()

    # Test: Admin accesses a protected route
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

def test_resident_cannot_access_admin_data(client, db, resident_token):
    # Setup: Create a resident user
    resident = User(
        email="resident1@solshare.com",
        hashed_password=get_password_hash("password123"),
        full_name="Resident User",
        role=UserRole.RESIDENT
    )
    db.add(resident)
    db.commit()

    # Test: Resident calls the User List (which should be admin only)
    # Note: Assuming /api/v1/users/ returns all users and is protected
    response = client.get("/api/v1/users/", headers={"Authorization": f"Bearer {resident_token}"})
    
    # If your RBAC is working, this should return a Forbidden (403) error
    assert response.status_code == 403
