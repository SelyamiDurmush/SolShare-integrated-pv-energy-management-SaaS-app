from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, UserRole, Building, Apartment
from app.schemas.billing_schema import BillingResponse
from app.api.deps import get_current_user
from app.services.billing import calculate_billing
from app.api.v1.analytics import _sum_readings
from app.models.energy import MeterType
from datetime import datetime, timedelta

router = APIRouter(prefix="/billing", tags=["billing"])

@router.post("/generate/{building_id}", response_model=BillingResponse)
def generate_billing_statement(
    building_id: int,
    month: int,
    year: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to generate bills")

    result = calculate_billing(building_id, month, year, db)
    if not result:
        raise HTTPException(status_code=404, detail="Building not found")

    return result

@router.get("/statements")
def get_billing_statements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Returns rolling 30-day estimated bills.
    Enforces RBAC:
    - Admin: all statements
    - Property Manager: only for buildings they manage
    - Resident: only for their own apartment
    """
    query = db.query(Apartment).join(Building)

    if current_user.role == UserRole.PROPERTY_MANAGER:
        query = query.filter(Building.manager_id == current_user.id)
    elif current_user.role == UserRole.RESIDENT:
        query = query.filter(Apartment.resident_id == current_user.id)

    apartments = query.all()

    now = datetime.utcnow()
    thirty_days_ago = now - timedelta(days=30)
    
    statements = []
    
    for apt in apartments:
        consumption = 0.0
        if apt.meter: # sum for this meter over 30 days
            from app.models.energy import MeterReading
            from sqlalchemy import func
            specific = (
                db.query(func.sum(MeterReading.value_kwh))
                .filter(MeterReading.meter_id == apt.meter.id)
                .filter(MeterReading.time >= thirty_days_ago)
                .scalar()
            ) or 0.0
            consumption = round(specific, 2)

        total_pv = 0.0
        total_consumption_building = 0.0
        building = apt.building
        if building:
            total_pv = _sum_readings(db, MeterType.PV_PRODUCTION, thirty_days_ago, now, building.id)
            total_consumption_building = _sum_readings(db, MeterType.APARTMENT, thirty_days_ago, now, building.id)
            
        solar_share = 0.0
        if total_consumption_building > 0 and consumption > 0:
            fraction = consumption / total_consumption_building
            solar_share = round(min(fraction * total_pv, consumption), 2)
            
        residual_grid = max(0.0, consumption - solar_share)
        
        solar_rate = 0.10 
        grid_rate = 0.35  
        
        total_cost = (solar_share * solar_rate) + (residual_grid * grid_rate)
        
        # Simple deterministic status for the PoC
        h = hash(str(apt.id) + apt.unit_number) % 3
        status = "Paid" if h == 0 else "Sent" if h == 1 else "Generated"
        
        statements.append({
            "id": apt.id,
            "unit": apt.unit_number,
            "building_name": building.name or building.address if building else "—",
            "resident": apt.resident.full_name if apt.resident else "Unassigned",
            "consumption": consumption,
            "solar_output": solar_share,
            "residual": round(residual_grid, 2),
            "total_cost": round(total_cost, 2),
            "status": status
        })
        
    return statements
