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


from app.services.energy import EnergyService
from app.models.energy import BatterySystem, BatteryReading


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
            production = EnergyService.sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = EnergyService.sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
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
            production = EnergyService.sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = EnergyService.sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
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
            production = EnergyService.sum_readings(db, MeterType.PV_PRODUCTION, bucket_start, bucket_end)
            consumption = EnergyService.sum_readings(db, MeterType.APARTMENT, bucket_start, bucket_end)
            data.append({
                "label": bucket_start.strftime("%b %d"),
                "production": production,
                "consumption": consumption,
            })

    total_prod = sum(d["production"] for d in data)
    total_cons = sum(d["consumption"] for d in data)
    self_sufficiency = 0
    if total_cons > 0:
        self_sufficiency = min(100, round((total_prod / total_cons) * 100))

    return {
        "period": period, 
        "data": data,
        "summary": {
            "total_production": round(total_prod, 2),
            "total_consumption": round(total_cons, 2),
            "self_sufficiency": self_sufficiency
        }
    }


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
            consumption = EnergyService.sum_readings(
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
            total_pv = EnergyService.sum_readings(db, MeterType.PV_PRODUCTION, week_ago, now, building.id)
            total_consumption_building = EnergyService.sum_readings(db, MeterType.APARTMENT, week_ago, now, building.id)

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

@router.get("/battery-status")
def get_battery_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Returns the latest battery status for the building.
    Covers all real-world BESS operating states.
    """
    battery = db.query(BatterySystem).first()
    if not battery:
        return {"status": "error", "message": "No battery system found"}

    latest_reading = (
        db.query(BatteryReading)
        .filter(BatteryReading.battery_id == battery.id)
        .order_by(BatteryReading.time.desc())
        .first()
    )

    if not latest_reading:
        return {"status": "error", "message": "No battery readings found"}

    soc = latest_reading.soc_percentage
    soh = latest_reading.soh_percentage
    power = latest_reading.power_kw

    # ── Determine status enum & label ──────────────────────────────────────
    # Priority order: fault → critically_low → full → charging → discharging → idle
    if soh < 60:
        # Battery health severely degraded — needs replacement
        status_enum = "fault"
        status_text = "Fault — Battery Health Critical"
    elif soc <= 5:
        # Near-empty — emergency condition
        status_enum = "critically_low"
        status_text = "Critically Low — Emergency Reserve"
    elif soc >= 99 and abs(power) <= 0.5:
        # Battery topped-up, no significant power flow
        status_enum = "full"
        status_text = "Fully Charged — Standby"
    elif power > 0.5:
        # Positive power_kw = battery is absorbing energy (charging)
        # Heuristic: if solar is available (daytime), assume solar source
        from datetime import datetime
        hour = datetime.utcnow().hour
        if 6 <= hour <= 20:
            status_enum = "charging"
            status_text = "Charging from Solar"
        else:
            status_enum = "charging_grid"
            status_text = "Charging from Grid"
    elif power < -0.5:
        # Negative power_kw = battery is supplying energy (discharging)
        status_enum = "discharging"
        status_text = "Discharging to Load"
    else:
        # Near-zero power flow
        status_enum = "idle"
        status_text = "Idle / Maintaining"

    available_kwh = (soc / 100.0) * battery.capacity_kwh

    return {
        "soc_percentage": round(soc, 1),
        "soh_percentage": round(soh, 1),
        "power_kw": round(power, 1),
        "estimated_backup_hours": round(latest_reading.estimated_backup_hours, 1),
        "status_text": status_text,
        "status_enum": status_enum,
        "available_kwh": round(available_kwh, 1),
        "capacity_kwh": battery.capacity_kwh,
        "updated_at": latest_reading.time.isoformat()
    }
