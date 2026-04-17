from pydantic import BaseModel, ConfigDict
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

    model_config = ConfigDict(from_attributes=True)

class MeterReadingCreate(BaseModel):
    meter_id: int
    time: datetime
    value_kwh: float

class MeterReading(MeterReadingCreate):
    model_config = ConfigDict(from_attributes=True)
