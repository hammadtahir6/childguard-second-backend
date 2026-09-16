from sqlalchemy import Column, Float, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class Location(Base):
    __tablename__ = "locations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    child_id = Column(UUID(as_uuid=True), ForeignKey("children.id"), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(String(300), nullable=True)
    speed = Column(Float, default=0.0)
    recorded_at = Column(DateTime(timezone=True),
                        server_default=func.now(), index=True)

    child = relationship("Child", back_populates="locations")