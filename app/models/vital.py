from sqlalchemy import Column, Float, Boolean, ForeignKey, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Vital(Base):
    __tablename__ = "vitals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id"), nullable=False)

    # Health sensors
    heart_rate = Column(Float, nullable=True)
    spo2 = Column(Float, nullable=True)
    temperature = Column(Float, nullable=True)

    # Motion sensors
    accel_x = Column(Float, nullable=True)
    accel_y = Column(Float, nullable=True)
    accel_z = Column(Float, nullable=True)
    gyro_x = Column(Float, nullable=True)
    gyro_y = Column(Float, nullable=True)
    gyro_z = Column(Float, nullable=True)

    # Other sensors
    sound_level = Column(Float, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # AI results
    fall_detected = Column(Boolean, default=False)
    anomaly_detected = Column(Boolean, default=False)
    behavior_abnormal = Column(Boolean, default=False)
    sound_alert = Column(Boolean, default=False)
    sound_type = Column(String(50), nullable=True)

    # Device status
    panic_pressed = Column(Boolean, default=False)
    band_on_wrist = Column(Boolean, default=True)
    battery_percent = Column(Float, nullable=True)

    recorded_at = Column(DateTime(timezone=True),
                        server_default=func.now(), index=True)

    child = relationship("Child", back_populates="vitals")