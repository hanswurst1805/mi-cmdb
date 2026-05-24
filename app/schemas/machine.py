from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.machine import MachineStatus


class MachineBase(BaseModel):
    fqdn: str
    hostname: str
    os: Optional[str] = None
    ram_gb: Optional[int] = None
    cpu_cores: Optional[int] = None
    status: MachineStatus = MachineStatus.active
    description: Optional[str] = None
    owner: Optional[str] = None


class MachineCreate(MachineBase):
    pass


class MachineUpdate(BaseModel):
    fqdn: Optional[str] = None
    hostname: Optional[str] = None
    os: Optional[str] = None
    ram_gb: Optional[int] = None
    cpu_cores: Optional[int] = None
    status: Optional[MachineStatus] = None
    description: Optional[str] = None
    owner: Optional[str] = None


class MachineResponse(MachineBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
