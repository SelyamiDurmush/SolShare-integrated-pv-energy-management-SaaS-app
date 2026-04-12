import sys
import os
from sqlalchemy.orm import Session
# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models import User, Building, Meter, MeterReading

def verify():
    db = SessionLocal()
    try:
        print("\n--- USERS ---")
        users = db.query(User).all()
        for u in users:
            print(f"[{u.role.value}] {u.email} (ID: {u.id})")
        
        print("\n--- BUILDINGS ---")
        buildings = db.query(Building).all()
        for b in buildings:
            print(f"ID: {b.id} | Address: {b.address}")
            
        print("\n--- STATS ---")
        print(f"Meters: {db.query(Meter).count()}")
        print(f"Readings: {db.query(MeterReading).count()}")

    finally:
        db.close()

if __name__ == "__main__":
    verify()