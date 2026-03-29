from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional

from app.core.database import get_db
from app.models.energy import Meter, MeterReading, MeterType
from app.models.building import Building, Apartment
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _sum_readings(db: Session, meter_type: MeterType, start: datetime, end: datetime, building_id: Optional[int] = None) -> float:
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


@router.get("/energy-overview")
def get_energy_overview(
    period: str = Query("daily", enum=["daily", "weekly", "monthly"]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns aggregated PV production & consumption data for the given period.
    - daily: last 24 hours, 1-hour buckets
    - weekly: last 7 days, 1-day buckets
    - monthly: last 30 days, 1-day buckets
    """
    now = datetime.utcnow()
    data = []

    if period == "daily":
        # 24 hourly buckets
        for h in range(23, -1, -1):
            bucket_start = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=h)
            bucket_end = bucket_start + timedelta(hours=1)
            production = _sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = _sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
            data.append({
                "label": bucket_start.strftime("%H:%M"),
                "production": production,
                "consumption": consumption,
            })

    elif period == "weekly":
        # 7 daily buckets
        for d in range(6, -1, -1):
            bucket_start = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            bucket_end = bucket_start + timedelta(days=1)
            production = _sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = _sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
            data.append({
                "label": bucket_start.strftime("%a %d"),
                "production": production,
                "consumption": consumption,
            })

    elif period == "monthly":
        # 30 daily buckets
        for d in range(29, -1, -1):
            bucket_start = (now - timedelta(days=d)).replace(hour=0, minute=0, second=0, microsecond=0)
            bucket_end = bucket_start + timedelta(days=1)
            production = _sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = _sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
            data.append({
                "label": bucket_start.strftime("%b %d"),
                "production": production,
                "consumption": consumption,
            })

    return {"period": period, "data": data}


@router.get("/apartment-usage")
def get_apartment_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns per-apartment energy consumption and solar share for the last 7 days,
    along with resident info from the database.
    """
    now = datetime.utcnow()
    week_ago = now - timedelta(days=7)

    apartments = db.query(Apartment).all()
    result = []

    for apt in apartments:
        # Get apartment meter consumption
        consumption = 0.0
        if apt.meter:
            consumption = _sum_readings(
                db, MeterType.APARTMENT, week_ago, now
            )
            # More precisely, sum for this specific meter
            specific = (
                db.query(func.sum(MeterReading.value_kwh))
                .filter(MeterReading.meter_id == apt.meter.id)
                .filter(MeterReading.time >= week_ago)
                .scalar()
            ) or 0.0
            consumption = round(specific, 2)

        # Get building PV production for solar share estimation
        building = apt.building
        total_pv = 0.0
        total_consumption_building = 0.0
        if building:
            total_pv = _sum_readings(db, MeterType.PV_PRODUCTION, week_ago, now, building.id)
            total_consumption_building = _sum_readings(db, MeterType.APARTMENT, week_ago, now, building.id)

        # Proportional solar share
        solar_share = 0.0
        if total_consumption_building > 0 and consumption > 0:
            fraction = consumption / total_consumption_building
            solar_share = round(min(fraction * total_pv, consumption), 2)

        result.append({
            "apartment_id": apt.id,
            "unit_number": apt.unit_number,
            "resident_name": apt.resident.full_name if apt.resident else None,
            "resident_email": apt.resident.email if apt.resident else None,
            "allocation_method": apt.allocation_method,
            "consumption_kwh": consumption,
            "solar_share_kwh": solar_share,
            "building_name": building.name or building.address if building else "—",
        })

    return result
