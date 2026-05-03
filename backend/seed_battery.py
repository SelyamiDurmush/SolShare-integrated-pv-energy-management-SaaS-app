import sys
import os
import random
from datetime import datetime, timedelta

# Add the backend directory to sys.path so 'app' package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal, engine, Base
from app.models.building import Building
from app.models.energy import BatterySystem, BatteryReading, Meter, MeterType

def seed_battery_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    if db.query(BatterySystem).first():
        print("Battery system already seeded. Skipping.")
        db.close()
        return
        
    building = db.query(Building).first()
    if not building:
        print("No building found. Run main seed.py first.")
        db.close()
        return

    print("Seeding battery system...")
    battery = BatterySystem(
        building_id=building.id,
        capacity_kwh=50.0
    )
    db.add(battery)
    db.commit()
    db.refresh(battery)

    pv_meter = db.query(Meter).filter(Meter.type == MeterType.PV_PRODUCTION).first()
    
    print("Generating 30 days of 15-minute battery readings (this may take a moment)...")

    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=30)
    current_time = start_time
    readings = []

    while current_time <= end_time:
        hour = current_time.hour
        
        # Approximate solar logic matching seed.py
        solar_kwh = 0.0
        if 6 <= hour <= 20:
            peak_factor = 1.0 - (abs(13 - hour) / 7.0)
            variation = 1.0 # assume 1.0 average to sync somewhat
            solar_kwh = max(0.0, peak_factor * 2.5 * variation)
            
        # Approximate consumption matching seed.py
        total_apt_consumption = 0.0
        for _ in range(5):
            base_load = 0.05
            activity = 0.0
            if 7 <= hour <= 9 or 18 <= hour <= 22:
                activity = 0.5
            elif 10 <= hour <= 17:
                activity = 0.15
            total_apt_consumption += base_load + activity

        net_power = solar_kwh - total_apt_consumption
        power_kw = net_power * 4.0
        
        hour_val = hour + current_time.minute / 60.0
        if 6 <= hour_val <= 14:
            soc = 20.0 + ((hour_val - 6) / 8.0) * 80.0
        elif 14 < hour_val <= 24:
            soc = 100.0 - ((hour_val - 14) / 10.0) * 60.0
        else:
            soc = 40.0 - (hour_val / 6.0) * 20.0
            
        estimated_backup = (soc / 100.0) * battery.capacity_kwh / max(0.5, total_apt_consumption * 4)

        readings.append(BatteryReading(
            time=current_time,
            battery_id=battery.id,
            soc_percentage=soc,
            soh_percentage=98.5 - (random.uniform(0, 0.5)),
            power_kw=power_kw,
            estimated_backup_hours=min(24.0, estimated_backup)
        ))

        current_time += timedelta(minutes=15)

        if len(readings) >= 5000:
            db.bulk_save_objects(readings)
            db.commit()
            readings = []

    if readings:
        db.bulk_save_objects(readings)
        db.commit()

    db.close()
    print("Successfully Battery seeding complete!")

if __name__ == "__main__":
    seed_battery_data()
