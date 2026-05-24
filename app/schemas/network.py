from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NetworkBase(BaseModel):
    name: str
    cidr: str
    gateway: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class NetworkCreate(NetworkBase):
    pass


class NetworkUpdate(BaseModel):
    name: Optional[str] = None
    cidr: Optional[str] = None
    gateway: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class NetworkResponse(NetworkBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
