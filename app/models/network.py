import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class Network(Base):
    __tablename__ = "networks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    cidr = Column(String(50), nullable=False, unique=True)
    gateway = Column(String(50))
    description = Column(Text)
    location = Column(String(255))
    embedding = Column(Vector(1536))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    ip_addresses = relationship("IPAddress", back_populates="network")

    def to_text(self) -> str:
        parts = [f"Netzwerk {self.name}", f"CIDR: {self.cidr}"]
        if self.gateway:
            parts.append(f"Gateway: {self.gateway}")
        if self.location:
            parts.append(f"Standort: {self.location}")
        if self.description:
            parts.append(f"Beschreibung: {self.description}")
        return ", ".join(parts)
