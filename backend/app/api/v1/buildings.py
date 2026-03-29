from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models import Building, Apartment, User, UserRole, AllocationMethod
from app.schemas.building_schema import Building as BuildingSchema, BuildingCreate
from app.api.deps import get_current_user

router = APIRouter(prefix="/buildings", tags=["buildings"])

@router.post("/", response_model=BuildingSchema)
def create_building(
    building_in: BuildingCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to create buildings")

    # 1. Create building record
    building_data = building_in.model_dump()
    units_count = building_data.pop("units_count")
    
    db_building = Building(**building_data, manager_id=current_user.id)
    db.add(db_building)
    db.commit()
    db.refresh(db_building)

    # 2. Automatically create apartments (mock units)
    for i in range(1, units_count + 1):
        apt = Apartment(
            building_id=db_building.id,
            unit_number=f"UNIT-{i}",
            allocation_method=AllocationMethod.DYNAMIC
        )
        db.add(apt)
    
    db.commit()
    db.refresh(db_building) # Refresh to get lazy-loaded apartments
    return db_building

@router.get("/", response_model=List[BuildingSchema])
def read_buildings(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == UserRole.PROPERTY_MANAGER:
        return db.query(Building).filter(Building.manager_id == current_user.id).offset(skip).limit(limit).all()
    return db.query(Building).offset(skip).limit(limit).all()
