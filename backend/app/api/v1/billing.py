from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User, UserRole, Building, Apartment
from app.schemas.billing_schema import BillingResponse
from app.api.deps import get_current_user
from app.services.billing import BillingService
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

    result = BillingService.calculate_billing(building_id, month, year, db)
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
    return BillingService.get_user_statements(db=db, user=current_user)
