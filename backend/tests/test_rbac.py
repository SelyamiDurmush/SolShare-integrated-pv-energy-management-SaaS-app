import pytest
from app.models.user import User, UserRole

def test_admin_can_access_admin_panel(client, admin_token):
    # Test: Admin accesses a protected route
    # The 'admin_token' fixture automatically creates the admin user
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["role"] == "admin"

def test_resident_cannot_access_admin_data(client, resident_token):
    # Test: Resident calls the User List (which should be admin only)
    # The 'resident_token' fixture automatically creates the resident user
    response = client.get("/api/v1/users/", headers={"Authorization": f"Bearer {resident_token}"})
    
    # If your RBAC is working, this should return a Forbidden (403) error
    assert response.status_code == 403
