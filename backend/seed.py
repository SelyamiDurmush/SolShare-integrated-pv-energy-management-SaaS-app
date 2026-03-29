import sys
import os
import random
from datetime import datetime, timedelta

# Add the backend directory to sys.path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.models.building import Building, Apartment, AllocationMethod
from app.models.energy import Meter, MeterReading, MeterType

def seed_data():
    # Ensure all tables exist
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    # Only seed if no Property Manager exists yet (admin is created by lifespan)
    if db.query(User).filter(User.role == UserRole.PROPERTY_MANAGER).first():
        print("Seed data already present (Property Manager found). Skipping.")
        db.close()
        return

    print("Seeding property manager and residents...")

    # 1. Property Manager
    manager = User(
        email="manager@solshare.com",
        hashed_password=get_password_hash("manager123"),
        full_name="Selyami Durmush",
        role=UserRole.PROPERTY_MANAGER
    )
    db.add(manager)
    db.commit()
    db.refresh(manager)

    # 2. Residents
    resident_names = ["Christoph Bimmermann", "Lukas Weber", "Marie Müller", "Tom Fischer", "Sara Klein"]
    residents = []
    for i, name in enumerate(resident_names, start=1):
        resident = User(
            email=f"resident{i}@solshare.com",
            hashed_password=get_password_hash("resident123"),
            full_name=name,
            role=UserRole.RESIDENT
        )
        db.add(resident)
        residents.append(resident)
    db.commit()
    for r in residents:
        db.refresh(r)

    print("Seeding building, apartments and meters...")

    # 3. Building
    building = Building(
        name="Philips Apartment",
        address="Philipsstraße 8, 52068 Aachen, Germany",
        manager_id=manager.id,
        grid_connection_capacity_kw=50.0
    )
    db.add(building)
    db.commit()
    db.refresh(building)

    # 4. Grid & PV meters
    grid_meter = Meter(
        serial_number="GRID-001",
        type=MeterType.GRID_MAIN,
        building_id=building.id
    )
    pv_meter = Meter(
        serial_number="PV-001",
        type=MeterType.PV_PRODUCTION,
        building_id=building.id
    )
    db.add(grid_meter)
    db.add(pv_meter)
    db.commit()
    db.refresh(grid_meter)
    db.refresh(pv_meter)

    # 5. Apartments & apartment meters
    apt_meters = []
    for i, resident in enumerate(residents):
        unit_number = f"10{i + 1}"
        apt = Apartment(
            building_id=building.id,
            unit_number=unit_number,
            resident_id=resident.id,
            allocation_method=AllocationMethod.DYNAMIC
        )
        db.add(apt)
        db.commit()
        db.refresh(apt)

        meter = Meter(
            serial_number=f"APT-{unit_number}",
            type=MeterType.APARTMENT,
            building_id=building.id,
            apartment_id=apt.id
        )
        db.add(meter)
        db.commit()
        db.refresh(meter)
        apt_meters.append(meter)

    print("Generating 7 days of 15-minute interval readings (this may take a moment)...")

    # 6. Generate readings for last 7 days at 15-min intervals
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=7)
    current_time = start_time
    readings = []

    while current_time <= end_time:
        hour = current_time.hour

        # Solar production — bell curve peaking around 13:00
        solar_kwh = 0.0
        if 6 <= hour <= 20:
            peak_factor = 1.0 - (abs(13 - hour) / 7.0)
            variation = random.uniform(0.8, 1.2)
            solar_kwh = max(0.0, peak_factor * 2.5 * variation)

        readings.append(MeterReading(
            time=current_time,
            meter_id=pv_meter.id,
            value_kwh=solar_kwh
        ))

        # Apartment consumption
        total_apt_consumption = 0.0
        for meter in apt_meters:
            base_load = 0.05
            activity = 0.0
            if 7 <= hour <= 9 or 18 <= hour <= 22:
                activity = random.uniform(0.2, 0.8)
            elif 10 <= hour <= 17:
                activity = random.uniform(0.0, 0.3)
            consumption = base_load + activity
            readings.append(MeterReading(
                time=current_time,
                meter_id=meter.id,
                value_kwh=consumption
            ))
            total_apt_consumption += consumption

        # Grid import (net of solar)
        grid_import = max(0.0, total_apt_consumption - solar_kwh)
        readings.append(MeterReading(
            time=current_time,
            meter_id=grid_meter.id,
            value_kwh=grid_import
        ))

        current_time += timedelta(minutes=15)

        # Batch insert every 5000 records
        if len(readings) >= 5000:
            db.bulk_save_objects(readings)
            db.commit()
            readings = []

    if readings:
        db.bulk_save_objects(readings)
        db.commit()

    db.close()
    print("Seeding complete!")
    print("\nSeeded accounts:")
    print(f"  Property Manager : manager@solshare.com  / manager123")
    for i, name in enumerate(resident_names, start=1):
        print(f"  Resident {i}       : resident{i}@solshare.com / resident123  ({name})")

if __name__ == "__main__":
    seed_data()