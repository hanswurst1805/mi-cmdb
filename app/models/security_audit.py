import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class SecurityAudit(Base):
    __tablename__ = "security_audits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    machine_id = Column(UUID(as_uuid=True), ForeignKey("machines.id", ondelete="CASCADE"), nullable=False)
    hardening_index = Column(Integer)          # 0-100
    lynis_version = Column(String(50))
    warnings = Column(JSON, default=list)      # Liste der Warnungen
    suggestions = Column(JSON, default=list)   # Liste der Verbesserungsvorschläge
    test_results = Column(JSON, default=dict)  # Rohe Testergebnisse
    audited_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    machine = relationship("Machine", back_populates="security_audits")
