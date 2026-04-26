from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
from typing import Optional

from app.models.energy import Meter, MeterReading, MeterType

class EnergyService:
    @staticmethod
    def sum_readings(db: Session, meter_type: MeterType, start: datetime, end: datetime, building_id: Optional[int] = None) -> float:
        query = (
            db.query(func.sum(MeterReading.value_kwh))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(Meter.type == meter_type)
            .filter(MeterReading.time >= start)
            .filter(MeterReading.time <= end)
        )
        if building_id:
            query = query.filter(Meter.building_id == building_id)
        result = query.scalar()
        return round(result or 0.0, 2)
