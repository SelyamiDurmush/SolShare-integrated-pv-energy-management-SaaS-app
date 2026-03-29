from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base


class AlertSeverity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    POSITIVE = "positive"


class AlertCategory(str, enum.Enum):
    METER_OFFLINE = "meter_offline"
    ABNORMAL_CONSUMPTION = "abnormal_consumption"
    GRID_OVERLOAD = "grid_overload"
    PV_UNDERPERFORMANCE = "pv_underperformance"
    UNASSIGNED_APARTMENT = "unassigned_apartment"
    BILLING_OVERDUE = "billing_overdue"
    MAINTENANCE = "maintenance"
    POSITIVE_RECORD = "positive_record"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    severity = Column(Enum(AlertSeverity), nullable=False)
    category = Column(Enum(AlertCategory), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)

    # Optional FK scope — at most one should be set
    building_id = Column(Integer, ForeignKey("buildings.id"), nullable=True)
    apartment_id = Column(Integer, ForeignKey("apartments.id"), nullable=True)
    meter_id = Column(Integer, ForeignKey("meters.id"), nullable=True)

    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)

    # Relationships for joins
    building = relationship("Building", foreign_keys=[building_id])
    apartment = relationship("Apartment", foreign_keys=[apartment_id])
    meter = relationship("Meter", foreign_keys=[meter_id])
