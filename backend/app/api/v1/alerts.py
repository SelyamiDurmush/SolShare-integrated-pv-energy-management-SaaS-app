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
from app.services.alerts import AlertsService

router = APIRouter(prefix="/alerts", tags=["alerts"])


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
    AlertsService.run_detection(db)

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
