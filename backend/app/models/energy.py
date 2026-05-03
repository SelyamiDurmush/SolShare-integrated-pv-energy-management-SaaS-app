from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime, Enum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class MeterType(str, enum.Enum):
    GRID_MAIN = "grid_main"      
    PV_PRODUCTION = "pv_production" 
    APARTMENT = "apartment"      

class Meter(Base):
    __tablename__ = "meters"

    id = Column(Integer, primary_key=True, index=True)
    serial_number = Column(String, unique=True, index=True)
    type = Column(Enum(MeterType), nullable=False)
    building_id = Column(Integer, ForeignKey("buildings.id"))
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=True)

    building = relationship("Building", back_populates="meters")
    apartment = relationship("Apartment", back_populates="meter")
    readings = relationship("MeterReading", back_populates="meter")

class MeterReading(Base):
    __tablename__ = "meter_readings"

    time = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    meter_id = Column(Integer, ForeignKey("meters.id"), primary_key=True)
    value_kwh = Column(Float, nullable=False)
    
    meter = relationship("Meter", back_populates="readings")

    __table_args__ = (UniqueConstraint('time', 'meter_id', name='_meter_time_uc'),)

class BatterySystem(Base):
    __tablename__ = "battery_systems"

    id = Column(Integer, primary_key=True, index=True)
    building_id = Column(Integer, ForeignKey("buildings.id"), unique=True)
    capacity_kwh = Column(Float, nullable=False)

    building = relationship("Building", back_populates="battery_system")
    readings = relationship("BatteryReading", back_populates="battery")

class BatteryReading(Base):
    __tablename__ = "battery_readings"

    time = Column(DateTime(timezone=True), primary_key=True, server_default=func.now())
    battery_id = Column(Integer, ForeignKey("battery_systems.id"), primary_key=True)
    
    soc_percentage = Column(Float, nullable=False) 
    soh_percentage = Column(Float, nullable=False) 
    power_kw = Column(Float, nullable=False) 
    estimated_backup_hours = Column(Float, nullable=False) 
    
    battery = relationship("BatterySystem", back_populates="readings")

    __table_args__ = (UniqueConstraint('time', 'battery_id', name='_battery_time_uc'),)
