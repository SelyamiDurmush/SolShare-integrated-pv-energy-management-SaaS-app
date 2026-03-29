from pydantic import BaseModel
from typing import Optional, List
from app.models.building import AllocationMethod

class ApartmentBase(BaseModel):
    unit_number: str
    allocation_method: AllocationMethod = AllocationMethod.DYNAMIC
    static_allocation_percentage: Optional[float] = None

class ApartmentCreate(ApartmentBase):
    building_id: int

class Apartment(ApartmentBase):
    id: int
    building_id: int
    resident_id: Optional[int] = None

    class Config:
        from_attributes = True

class BuildingBase(BaseModel):
    name: str  # Required
    address: str
    grid_connection_capacity_kw: float  # Required

class BuildingCreate(BuildingBase):
    units_count: int  # Required for creation

class Building(BuildingBase):
    id: int
    manager_id: int
    apartments: List[Apartment] = []

    class Config:
        from_attributes = True
