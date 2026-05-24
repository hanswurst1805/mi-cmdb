import uuid
from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class IPType(str, PyEnum):
    ipv4 = "ipv4"
    ipv6 = "ipv6"


class IPAddress(Base):
    __tablename__ = "ip_addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nic_id = Column(UUID(as_uuid=True), ForeignKey("nics.id", ondelete="CASCADE"), nullable=False)
    network_id = Column(UUID(as_uuid=True), ForeignKey("networks.id", ondelete="SET NULL"), nullable=True)
    address = Column(String(45), nullable=False, index=True)
    type = Column(Enum(IPType), default=IPType.ipv4, nullable=False)
    deleted_at = Column(DateTime, nullable=True)

    nic = relationship("NIC", back_populates="ip_addresses")
    network = relationship("Network", back_populates="ip_addresses")
