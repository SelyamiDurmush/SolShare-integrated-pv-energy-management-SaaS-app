import os
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import SessionLocal, Base, engine
from app.models import Alert, AlertSeverity, AlertCategory, Building, Apartment

def seed_alerts():
    db = SessionLocal()
    try:
        building = db.query(Building).first()
        apartments = db.query(Apartment).all()
        now = datetime.utcnow()

        if not building:
            print("❌ No building found to attach alerts to.")
            return
            
        print("Seeding mock alerts...")
        
        # Clear existing mock alerts
        db.query(Alert).delete()

        # 1. Critical (Overdue) - Battery Check
        alert1 = Alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.MAINTENANCE,
            title="Battery Voltage Check",
            message="Inspect battery connections and voltage levels. Critical for system reliability.",
            building_id=building.id,
            created_at=now - timedelta(days=5),
            is_resolved=False
        )

        # 2. Warning (Pending) - Solar Panel Cleaning
        alert2 = Alert(
            severity=AlertSeverity.WARNING,
            category=AlertCategory.MAINTENANCE,
            title="Solar Panel Cleaning",
            message="Clean dust and debris from solar panels for optimal efficiency. May reduce generation by 15-20%.",
            building_id=building.id,
            created_at=now - timedelta(days=2),
            is_resolved=False
        )

        # 3. Info (Scheduled) - System Calibration
        alert3 = Alert(
            severity=AlertSeverity.INFO,
            category=AlertCategory.MAINTENANCE,
            title="System Calibration",
            message="Calibrate sensors and verify measurement accuracy. Ensures accurate monitoring.",
            building_id=building.id,
            created_at=now + timedelta(days=2), # Future date to indicate scheduled
            is_resolved=False
        )
        
        # 4. Critical - Grid Overload (Building wide)
        alert4 = Alert(
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.GRID_OVERLOAD,
            title="Grid Overload Risk",
            message=f"{building.name}: Net grid draw exceeded capacity limits during peak hours yesterday.",
            building_id=building.id,
            created_at=now - timedelta(hours=14),
            is_resolved=False
        )

        db.add_all([alert1, alert2, alert3, alert4])
        
        # 5. Apartment specific alerts
        for apt in apartments[:2]:
            alert_apt = Alert(
                severity=AlertSeverity.WARNING,
                category=AlertCategory.ABNORMAL_CONSUMPTION,
                title="Abnormal Consumption Detected",
                message=f"Apt {apt.unit_number} consumed 42% above its 7-day average yesterday.",
                building_id=building.id,
                apartment_id=apt.id,
                created_at=now - timedelta(hours=6),
                is_resolved=False
            )
            db.add(alert_apt)

        db.commit()
        print("Successfully seeded mock alerts!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_alerts()
