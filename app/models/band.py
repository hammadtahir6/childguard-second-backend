from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Band(Base):
    __tablename__ = "bands"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True),
                     ForeignKey("children.id"), nullable=True, unique=True)
    band_code = Column(String(20), unique=True, nullable=False, index=True)
    firmware_version = Column(String(20), default="1.0.0")
    battery_level = Column(Integer, default=100)
    is_connected = Column(Boolean, default=False)
    is_paired = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    child = relationship("Child", back_populates="band")