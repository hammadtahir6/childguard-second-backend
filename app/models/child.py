from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid, enum
from app.database import Base

class ChildStatus(str, enum.Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    EMERGENCY = "EMERGENCY"

class Child(Base):
    __tablename__ = "children"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), nullable=False)
    grade = Column(String(50), nullable=True)
    school_name = Column(String(200), nullable=True)
    school_start_time = Column(String(10), nullable=True)
    school_end_time = Column(String(10), nullable=True)
    status = Column(Enum(ChildStatus), default=ChildStatus.SAFE)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("User", back_populates="children")
    band = relationship("Band", back_populates="child",
                       uselist=False, cascade="all, delete-orphan")
    vitals = relationship("Vital", back_populates="child",
                         cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="child",
                         cascade="all, delete-orphan")
    locations = relationship("Location", back_populates="child",
                            cascade="all, delete-orphan")