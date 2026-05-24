import uuid
from datetime import datetime
from enum import Enum as PyEnum

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, Enum, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class MachineStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"
    decommissioned = "decommissioned"


class Machine(Base):
    __tablename__ = "machines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fqdn = Column(String(255), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=False)
    os = Column(String(255))
    ram_gb = Column(Integer)
    cpu_cores = Column(Integer)
    status = Column(Enum(MachineStatus), default=MachineStatus.active, nullable=False)
    description = Column(Text)
    owner = Column(String(255))
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    deleted_at = Column(DateTime, nullable=True, index=True)

    nics = relationship("NIC", back_populates="machine", cascade="all, delete-orphan")
    security_audits = relationship("SecurityAudit", back_populates="machine", cascade="all, delete-orphan", order_by="SecurityAudit.audited_at.desc()")

    def to_text(self) -> str:
        """Erzeugt eine Textrepräsentation für das Embedding."""
        parts = [f"Server {self.fqdn}"]
        if self.hostname:
            parts.append(f"Hostname: {self.hostname}")
        if self.os:
            parts.append(f"OS: {self.os}")
        if self.ram_gb:
            parts.append(f"RAM: {self.ram_gb}GB")
        if self.cpu_cores:
            parts.append(f"CPUs: {self.cpu_cores}")
        if self.status:
            parts.append(f"Status: {self.status.value}")
        if self.owner:
            parts.append(f"Owner: {self.owner}")
        if self.description:
            parts.append(f"Beschreibung: {self.description}")
        return ", ".join(parts)
