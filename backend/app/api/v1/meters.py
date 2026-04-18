from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.core.database import get_db
from app.models import Meter, MeterReading, User, UserRole
from app.models.building import Building, Apartment
from app.schemas.energy_schema import Meter as MeterSchema, MeterCreate, MeterReading as MeterReadingSchema, MeterReadingCreate
from app.api.deps import get_current_user

router = APIRouter(prefix="/meters", tags=["meters"])

@router.post("/", response_model=MeterSchema)
def create_meter(
    meter: MeterCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to add meters")

    db_meter = Meter(**meter.model_dump())
    db.add(db_meter)
    db.commit()
    db.refresh(db_meter)
    return db_meter

@router.post("/{meter_id}/readings", response_model=MeterReadingSchema)
def add_meter_reading(
    meter_id: int,
    reading: MeterReadingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    
    # Only Admin or the resident assigned to this meter's apartment can add readings
    if current_user.role != UserRole.ADMIN:
        if not meter.apartment_id or db.query(Apartment).filter(Apartment.id == meter.apartment_id, Apartment.resident_id == current_user.id).count() == 0:
             raise HTTPException(status_code=403, detail="Not authorized to submit readings for this meter")

    db_reading = MeterReading(
        meter_id=meter_id,
        time=reading.time,
        value_kwh=reading.value_kwh
    )
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

@router.get("/{meter_id}/readings", response_model=List[MeterReadingSchema])
def get_meter_readings(
    meter_id: int,
    start_time: datetime = None,
    end_time: datetime = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")

    # Security check: Residents can only see their own meter data
    if current_user.role == UserRole.RESIDENT:
        # Check if this meter belongs to an apartment owned by the current user
        from app.models.building import Apartment
        is_owner = db.query(Apartment).filter(
            Apartment.id == meter.apartment_id, 
            Apartment.resident_id == current_user.id
        ).first()
        if not is_owner:
            raise HTTPException(status_code=403, detail="Access denied to this meter's data")

    query = db.query(MeterReading).filter(MeterReading.meter_id == meter_id)
    
    if start_time:
        query = query.filter(MeterReading.time >= start_time)
    if end_time:
        query = query.filter(MeterReading.time <= end_time)
        
    return query.order_by(MeterReading.time.desc()).limit(1000).all()
