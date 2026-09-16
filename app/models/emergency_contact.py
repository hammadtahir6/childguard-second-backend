from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class EmergencyContact(Base):
    __tablename__ = "emergency_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    relation = Column(String(50), nullable=False)
    phone = Column(String(20), nullable=False)
    is_primary = Column(Boolean, default=False)
    alert_order = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="emergency_contacts")