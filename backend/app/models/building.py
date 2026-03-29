from sqlalchemy import Column, ForeignKey, Integer, String, Float, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class AllocationMethod(str, enum.Enum):
    STATIC = "static"
    DYNAMIC = "dynamic"

class Building(Base):
    __tablename__ = "buildings"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    address = Column(String, nullable=False)
    manager_id = Column(Integer, ForeignKey("users.id"))
    
    grid_connection_capacity_kw = Column(Float)

    # Relationships
    manager = relationship("User", back_populates="managed_buildings")
    apartments = relationship("Apartment", back_populates="building")
    meters = relationship("Meter", back_populates="building")

class Apartment(Base):
    __tablename__ = "apartments"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    unit_number = Column(String, nullable=False)
    resident_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    allocation_method = Column(Enum(AllocationMethod), default=AllocationMethod.DYNAMIC)
    static_allocation_percentage = Column(Float, nullable=True)

    # Relationships
    building = relationship("Building", back_populates="apartments")
    resident = relationship("User", back_populates="apartment")
    meter = relationship("Meter", back_populates="apartment", uselist=False)
