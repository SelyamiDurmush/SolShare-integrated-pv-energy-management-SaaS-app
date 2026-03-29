import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.database import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
for u in users:
    print(f"ID: {u.id}, Email: {u.email}, Name: {u.full_name}, Role: {u.role}")
db.close()
