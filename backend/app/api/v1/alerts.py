"""
System Alerts — Phase 1 (DB Polling)

Detection runs on-demand when the GET /alerts endpoint is called.
New unique alerts are upserted  (deduped by category + scope key).
RBAC:
  - admin / property_manager  → all alerts
  - resident                  → only alerts scoped to their apartment(s)
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.models import (
    Alert, AlertSeverity, AlertCategory,
    Meter, MeterReading, MeterType,
    Building, Apartment,
    User, UserRole,
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ── Detection helpers ──────────────────────────────────────────────────────────

def _upsert_alert(
    db: Session,
    *,
    severity: AlertSeverity,
    category: AlertCategory,
    title: str,
    message: str,
    building_id: Optional[int] = None,
    apartment_id: Optional[int] = None,
    meter_id: Optional[int] = None,
) -> None:
    """Create alert only if an active (unresolved) one with the same scope doesn't exist."""
    existing = (
        db.query(Alert)
        .filter(
            Alert.category == category,
            Alert.is_resolved == False,
            Alert.building_id == building_id,
            Alert.apartment_id == apartment_id,
            Alert.meter_id == meter_id,
        )
        .first()
    )
    if existing:
        return  # already open — don't duplicate

    alert = Alert(
        severity=severity,
        category=category,
        title=title,
        message=message,
        building_id=building_id,
        apartment_id=apartment_id,
        meter_id=meter_id,
    )
    db.add(alert)


def run_detection(db: Session) -> None:
    """Run all detection checks and upsert alerts into the DB."""
    now = datetime.utcnow()

    # ── 1. Meter offline: no readings in last 2 hours ─────────────────────────
    two_hours_ago = now - timedelta(hours=2)
    apt_meters = db.query(Meter).filter(Meter.type == MeterType.APARTMENT).all()
    for meter in apt_meters:
        latest = (
            db.query(func.max(MeterReading.time))
            .filter(MeterReading.meter_id == meter.id)
            .scalar()
        )
        if latest is None or latest < two_hours_ago:
            apt_label = meter.apartment.unit_number if meter.apartment else meter.serial_number
            _upsert_alert(
                db,
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.METER_OFFLINE,
                title="Meter Offline",
                message=f"No readings received from meter {meter.serial_number} (Apt {apt_label}) in the last 2 hours.",
                building_id=meter.building_id,
                apartment_id=meter.apartment_id,
                meter_id=meter.id,
            )
        else:
            # Auto-resolve if meter is back
            db.query(Alert).filter(
                Alert.category == AlertCategory.METER_OFFLINE,
                Alert.meter_id == meter.id,
                Alert.is_resolved == False,
            ).update({"is_resolved": True, "resolved_at": now})

    # ── 2. Abnormal consumption: >40% above 7-day average ────────────────────
    one_day_ago = now - timedelta(hours=24)
    seven_days_ago = now - timedelta(days=7)

    for apt in db.query(Apartment).all():
        if not apt.meter:
            continue

        day_sum = (
            db.query(func.sum(MeterReading.value_kwh))
            .filter(MeterReading.meter_id == apt.meter.id, MeterReading.time >= one_day_ago)
            .scalar()
        ) or 0.0

        week_avg_daily = (
            (db.query(func.sum(MeterReading.value_kwh))
             .filter(MeterReading.meter_id == apt.meter.id, MeterReading.time >= seven_days_ago)
             .scalar() or 0.0) / 7.0
        )

        if week_avg_daily > 0 and day_sum > week_avg_daily * 1.4:
            pct = round(((day_sum / week_avg_daily) - 1) * 100)
            _upsert_alert(
                db,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.ABNORMAL_CONSUMPTION,
                title="Abnormal Consumption Detected",
                message=f"Apt {apt.unit_number} consumed {day_sum:.1f} kWh today — {pct}% above its 7-day average ({week_avg_daily:.1f} kWh/day).",
                building_id=apt.building_id,
                apartment_id=apt.id,
            )

    # ── 3. Grid overload: current hour draw > capacity ────────────────────────
    one_hour_ago = now - timedelta(hours=1)
    for building in db.query(Building).all():
        if not building.grid_connection_capacity_kw:
            continue

        total_draw = (
            db.query(func.sum(MeterReading.value_kwh))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(
                Meter.building_id == building.id,
                Meter.type == MeterType.APARTMENT,
                MeterReading.time >= one_hour_ago,
            )
            .scalar()
        ) or 0.0

        pv_last_hour = (
            db.query(func.sum(MeterReading.value_kwh))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(
                Meter.building_id == building.id,
                Meter.type == MeterType.PV_PRODUCTION,
                MeterReading.time >= one_hour_ago,
            )
            .scalar()
        ) or 0.0

        net_grid = max(0, total_draw - pv_last_hour)
        if net_grid > building.grid_connection_capacity_kw:
            _upsert_alert(
                db,
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.GRID_OVERLOAD,
                title="Grid Overload Risk",
                message=(
                    f"{building.name or building.address}: Net grid draw {net_grid:.1f} kWh "
                    f"exceeds capacity {building.grid_connection_capacity_kw} kWh in the last hour."
                ),
                building_id=building.id,
            )
        else:
            db.query(Alert).filter(
                Alert.category == AlertCategory.GRID_OVERLOAD,
                Alert.building_id == building.id,
                Alert.is_resolved == False,
            ).update({"is_resolved": True, "resolved_at": now})

    # ── 4. PV underperformance: production < 60% of capacity estimate ─────────
    for building in db.query(Building).all():
        if not building.grid_connection_capacity_kw:
            continue

        pv_today = (
            db.query(func.sum(MeterReading.value_kwh))
            .join(Meter, Meter.id == MeterReading.meter_id)
            .filter(
                Meter.building_id == building.id,
                Meter.type == MeterType.PV_PRODUCTION,
                MeterReading.time >= now.replace(hour=0, minute=0, second=0, microsecond=0),
            )
            .scalar()
        ) or 0.0

        # Rough daytime expected: capacity_kw * peak_sun_hours (6h) * efficiency (0.8)
        expected = building.grid_connection_capacity_kw * 6 * 0.8
        if expected > 0 and pv_today < expected * 0.6 and now.hour >= 14:
            pct = round((pv_today / expected) * 100)
            _upsert_alert(
                db,
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PV_UNDERPERFORMANCE,
                title="PV System Underperforming",
                message=(
                    f"{building.name or building.address}: Today's solar output is {pv_today:.1f} kWh "
                    f"({pct}% of expected {expected:.1f} kWh)."
                ),
                building_id=building.id,
            )

    # ── 5. Unassigned apartments ───────────────────────────────────────────────
    unassigned = db.query(Apartment).filter(Apartment.resident_id == None).all()
    for apt in unassigned:
        _upsert_alert(
            db,
            severity=AlertSeverity.INFO,
            category=AlertCategory.UNASSIGNED_APARTMENT,
            title="Unassigned Apartment",
            message=f"Apt {apt.unit_number} in {apt.building.name or apt.building.address} has no resident assigned.",
            building_id=apt.building_id,
            apartment_id=apt.id,
        )

    db.commit()


# ── API Endpoints ──────────────────────────────────────────────────────────────

@router.get("/")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    include_resolved: bool = False,
):
    """
    Run detection then return alerts filtered by role:
    - admin / property_manager: all alerts
    - resident: only alerts scoped to their own apartment(s)
    """
    run_detection(db)

    query = db.query(Alert)
    if not include_resolved:
        query = query.filter(Alert.is_resolved == False)

    if current_user.role == UserRole.RESIDENT:
        # Find apartments belonging to this resident
        resident_apt_ids = [
            apt.id for apt in db.query(Apartment).filter(Apartment.resident_id == current_user.id).all()
        ]
        if not resident_apt_ids:
            return []
        query = query.filter(Alert.apartment_id.in_(resident_apt_ids))

    alerts = query.order_by(Alert.created_at.desc()).limit(50).all()

    def _serialize(a: Alert):
        return {
            "id": a.id,
            "severity": a.severity,
            "category": a.category,
            "title": a.title,
            "message": a.message,
            "is_read": a.is_read,
            "is_resolved": a.is_resolved,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "resolved_at": a.resolved_at.isoformat() if a.resolved_at else None,
            "building_id": a.building_id,
            "apartment_id": a.apartment_id,
            "meter_id": a.meter_id,
        }

    return [_serialize(a) for a in alerts]


@router.patch("/{alert_id}/read")
def mark_read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_read = True
        db.commit()
    return {"ok": True}


@router.patch("/{alert_id}/resolve")
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.RESIDENT:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Residents cannot resolve alerts.")
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert:
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        db.commit()
    return {"ok": True}
