from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

from app.models.ip_address import IPType


class IPAddressBase(BaseModel):
    address: str
    type: IPType = IPType.ipv4
    network_id: Optional[UUID] = None


class IPAddressCreate(IPAddressBase):
    nic_id: UUID


class IPAddressResponse(IPAddressBase):
    id: UUID
    nic_id: UUID
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
