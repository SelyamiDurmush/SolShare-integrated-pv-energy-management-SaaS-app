from sqlalchemy import Boolean, Column, Integer, String, Enum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    PROPERTY_MANAGER = "property_manager"
    RESIDENT = "resident"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    role = Column(Enum(UserRole), default=UserRole.RESIDENT)
    is_active = Column(Boolean, default=True)

    # Relationships
    managed_buildings = relationship("Building", back_populates="manager")
    apartment = relationship("Apartment", back_populates="resident", uselist=False)
