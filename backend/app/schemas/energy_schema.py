from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.energy import MeterType

class MeterBase(BaseModel):
    serial_number: str
    type: MeterType

class MeterCreate(MeterBase):
    building_id: int
    apartment_id: Optional[int] = None

class Meter(MeterBase):
    id: int
    building_id: int
    apartment_id: Optional[int] = None

    class Config:
        from_attributes = True

class MeterReadingCreate(BaseModel):
    meter_id: int
    time: datetime
    value_kwh: float

class MeterReading(MeterReadingCreate):
    class Config:
        from_attributes = True
