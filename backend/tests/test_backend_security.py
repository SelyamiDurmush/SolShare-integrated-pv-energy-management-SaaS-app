import pytest
from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.energy import Meter, MeterReading, MeterType
from app.models.building import Building, Apartment

def test_schema_rejects_negative_energy(client, admin_token, db):
    # Setup: Create a building first so the foreign key is valid
    building = Building(name="Test Building", address="123 Test St", grid_connection_capacity_kw=100.0)
    db.add(building)
    db.commit()
    db.refresh(building)

    meter = Meter(serial_number="STRESS_001", type=MeterType.APARTMENT, building_id=building.id)
    db.add(meter)
    db.commit()
    db.refresh(meter)

    # Stress Test: Reject negative consumption
    bad_reading = {
        "meter_id": meter.id,
        "time": datetime.utcnow().isoformat(),
        "value_kwh": -500.0
    }
    # Using the correct endpoint: POST /api/v1/meters/{id}/readings
    response = client.post(f"/api/v1/meters/{meter.id}/readings", json=bad_reading, headers={"Authorization": f"Bearer {admin_token}"})
    
    # Pydantic V2 returns 422 for validation errors
    assert response.status_code == 422
    assert "greater_than_equal" in str(response.json())

def test_data_isolation_residents_energy(client, db, resident_token):
    # Isolation: Resident 1 should not see Resident 2's meter data
    
    # 1. Create Building and Resident 2 
    building = Building(name="Test Building", address="123 Test St", grid_connection_capacity_kw=100.0)
    db.add(building)
    db.commit()
    db.refresh(building)

    res_2 = User(email="resident2@solshare.com", hashed_password="...", role=UserRole.RESIDENT, full_name="Resident 2")
    db.add(res_2)
    db.commit()
    
    apt_2 = Apartment(unit_number="102", building_id=building.id, resident_id=res_2.id)
    db.add(apt_2)
    db.commit()
    
    meter_2 = Meter(serial_number="MTR_RES_2", type=MeterType.APARTMENT, building_id=building.id, apartment_id=apt_2.id)
    db.add(meter_2)
    db.commit()
    
    # 2. Try to fetch Resident 2's data using Resident 1's token
    response = client.get(f"/api/v1/meters/{meter_2.id}/readings", headers={"Authorization": f"Bearer {resident_token}"})
    
    # Security check: Expect 403 Forbidden
    assert response.status_code == 403

def test_energy_math_self_sufficiency(client, db, admin_token):
    # Math: Verify 50kWh Prod / 100kWh Cons = 50% Self Sufficiency
    # Note: We use Admin token to bypass owner checks for building-wide analytics
    
    # 1. Setup mock Building and meters
    building = Building(name="Math Building", address="Math St", grid_connection_capacity_kw=100.0)
    db.add(building)
    db.commit()
    db.refresh(building)

    meter_pv = Meter(serial_number="PV_MOCK", type=MeterType.PV_PRODUCTION, building_id=building.id)
    meter_apt = Meter(serial_number="APT_MOCK", type=MeterType.APARTMENT, building_id=building.id)
    db.add(meter_pv)
    db.add(meter_apt)
    db.commit()
    
    # 2. Add readings for today (Analytics uses UTC now)
    now = datetime.utcnow()
    db.add(MeterReading(meter_id=meter_pv.id, value_kwh=50.0, time=now))
    db.add(MeterReading(meter_id=meter_apt.id, value_kwh=100.0, time=now))
    db.commit()
    
    # 3. Call Analytics
    response = client.get("/api/v1/analytics/energy-overview?period=daily", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    
    summary = response.json()["summary"]
    assert summary["total_production"] == 50.0
    assert summary["total_consumption"] == 100.0
    assert summary["self_sufficiency"] == 50 # (Math: 50 / 100 * 100)

def test_jwt_expiration_security(client):
    # Security: Test that expired tokens are rejected
    # 1. Create a token that expired 1 hour ago
    expire = datetime.utcnow() - timedelta(hours=1)
    to_encode = {"sub": "admin@solshare.com", "exp": expire}
    expired_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    # 2. Try to use it
    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    
    # 401 Unauthorized is expected for expired tokens
    assert response.status_code == 401
