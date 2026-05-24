from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class NICBase(BaseModel):
    name: str
    mac_address: Optional[str] = None


class NICCreate(NICBase):
    machine_id: UUID


class NICResponse(NICBase):
    id: UUID
    machine_id: UUID

    model_config = {"from_attributes": True}
