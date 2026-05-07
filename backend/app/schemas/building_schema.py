from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from app.models.building import AllocationMethod

class ApartmentBase(BaseModel):
    unit_number: str
    allocation_method: AllocationMethod = AllocationMethod.DYNAMIC
    static_allocation_percentage: Optional[float] = None

class ApartmentCreate(ApartmentBase):
    building_id: int
    resident_name: Optional[str] = None

class ApartmentUpdate(BaseModel):
    unit_number: Optional[str] = None
    resident_id: Optional[int] = None
    resident_name: Optional[str] = None
    allocation_method: Optional[AllocationMethod] = None
    static_allocation_percentage: Optional[float] = None

class Apartment(ApartmentBase):
    id: int
    building_id: int
    resident_id: Optional[int] = None
    resident_name: Optional[str] = None  # Helper for UI display

    model_config = ConfigDict(from_attributes=True)

class BuildingBase(BaseModel):
    name: str  # Required
    address: str
    grid_connection_capacity_kw: float  # Required

class BuildingCreate(BuildingBase):
    pass

class BuildingUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    grid_connection_capacity_kw: Optional[float] = None
    is_active: Optional[bool] = None

class Building(BuildingBase):
    id: int
    manager_id: int
    is_active: bool
    apartments: List[Apartment] = []

    model_config = ConfigDict(from_attributes=True)
