import uuid

from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class NIC(Base):
    __tablename__ = "nics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    mac_address = Column(String(17))

    machine = relationship("Machine", back_populates="nics")
    ip_addresses = relationship("IPAddress", back_populates="nic", cascade="all, delete-orphan")
