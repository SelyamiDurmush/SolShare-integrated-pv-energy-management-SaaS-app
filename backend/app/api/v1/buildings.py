from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import Building, Apartment, User, UserRole, AllocationMethod
from app.schemas.building_schema import Building as BuildingSchema, BuildingCreate, BuildingUpdate, Apartment as ApartmentSchema, ApartmentCreate, ApartmentUpdate
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
    
    db_building = Building(**building_data, manager_id=current_user.id)
    db.add(db_building)
    db.commit()
    db.refresh(db_building)

    db.commit()
    db.refresh(db_building) 
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

@router.patch("/{building_id}", response_model=BuildingSchema)
def update_building(
    building_id: int,
    building_in: BuildingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to update buildings")

    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
        
    if current_user.role == UserRole.PROPERTY_MANAGER and building.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to update this building")

    update_data = building_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(building, field, value)
        
    db.commit()
    db.refresh(building)
    return building

@router.delete("/{building_id}")
def delete_building(
    building_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized to delete buildings")

    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
        
    if current_user.role == UserRole.PROPERTY_MANAGER and building.manager_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this building")

    db.delete(building)
    db.commit()
    return {"ok": True}

@router.post("/{building_id}/apartments", response_model=ApartmentSchema)
def create_apartment(
    building_id: int,
    apartment_in: ApartmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    building = db.query(Building).filter(Building.id == building_id).first()
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")

    apt_data = apartment_in.model_dump()
    resident_name = apt_data.pop("resident_name", None)
    
    if resident_name:
        # Resolve resident
        resident = db.query(User).filter(User.full_name == resident_name, User.role == UserRole.RESIDENT).first()
        if not resident:
            # Create a mock user for this name
            safe_name = resident_name.lower().replace(" ", ".")
            email = f"{safe_name}.{apt_data['unit_number']}@solshare.app"
            # Ensure unique email
            count = 1
            base_email = email
            while db.query(User).filter(User.email == email).first():
                email = f"{safe_name}.{apt_data['unit_number']}.{count}@solshare.app"
                count += 1
            
            resident = User(
                email=email,
                full_name=resident_name,
                hashed_password=get_password_hash("resident123"),
                role=UserRole.RESIDENT
            )
            db.add(resident)
            db.commit()
            db.refresh(resident)
        apt_data["resident_id"] = resident.id

    db_apartment = Apartment(**apt_data)
    db.add(db_apartment)
    db.commit()
    db.refresh(db_apartment)
    return db_apartment

@router.patch("/{building_id}/apartments/{apartment_id}", response_model=ApartmentSchema)
def update_apartment(
    building_id: int,
    apartment_id: int,
    apartment_in: ApartmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    apartment = db.query(Apartment).filter(
        Apartment.id == apartment_id, 
        Apartment.building_id == building_id
    ).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")

    update_data = apartment_in.model_dump(exclude_unset=True)
    resident_name = update_data.pop("resident_name", None)
    
    if resident_name:
        resident = db.query(User).filter(User.full_name == resident_name, User.role == UserRole.RESIDENT).first()
        if not resident:
            safe_name = resident_name.lower().replace(" ", ".")
            email = f"{safe_name}.{apartment.unit_number}@solshare.app"
            count = 1
            while db.query(User).filter(User.email == email).first():
                email = f"{safe_name}.{apartment.unit_number}.{count}@solshare.app"
                count += 1
            
            resident = User(
                email=email,
                full_name=resident_name,
                hashed_password=get_password_hash("resident123"),
                role=UserRole.RESIDENT
            )
            db.add(resident)
            db.commit()
            db.refresh(resident)
        update_data["resident_id"] = resident.id

    for field, value in update_data.items():
        setattr(apartment, field, value)
    
    db.commit()
    db.refresh(apartment)
    return apartment

@router.delete("/{building_id}/apartments/{apartment_id}")
def delete_apartment(
    building_id: int,
    apartment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.PROPERTY_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    apartment = db.query(Apartment).filter(
        Apartment.id == apartment_id, 
        Apartment.building_id == building_id
    ).first()
    if not apartment:
        raise HTTPException(status_code=404, detail="Apartment not found")

    resident_id = apartment.resident_id
    
    # 1. Delete the apartment
    db.delete(apartment)
    
    # 2. If there was a resident, delete the user record too
    if resident_id:
        resident = db.query(User).filter(User.id == resident_id).first()
        if resident:
            db.delete(resident)
            
    db.commit()
    return {"ok": True}
