from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid, enum
from app.database import Base

class AlertSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"

class AlertType(str, enum.Enum):
    FALL_DETECTED = "FALL_DETECTED"
    SOS_PRESSED = "SOS_PRESSED"
    TAMPER_DETECTED = "TAMPER_DETECTED"
    LEFT_SAFE_ZONE = "LEFT_SAFE_ZONE"
    HIGH_HEART_RATE = "HIGH_HEART_RATE"
    LOW_HEART_RATE = "LOW_HEART_RATE"
    LOW_SPO2 = "LOW_SPO2"
    HIGH_TEMPERATURE = "HIGH_TEMPERATURE"
    BAND_REMOVED = "BAND_REMOVED"
    UNUSUAL_STILLNESS = "UNUSUAL_STILLNESS"
    SCREAM_DETECTED = "SCREAM_DETECTED"
    CRYING_DETECTED = "CRYING_DETECTED"
    ANOMALY_DETECTED = "ANOMALY_DETECTED"
    BATTERY_LOW = "BATTERY_LOW"

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id"), nullable=False)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    heart_rate_at_alert = Column(Float, nullable=True)
    spo2_at_alert = Column(Float, nullable=True)
    temperature_at_alert = Column(Float, nullable=True)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True),
                       server_default=func.now(), index=True)

    child = relationship("Child", back_populates="alerts")