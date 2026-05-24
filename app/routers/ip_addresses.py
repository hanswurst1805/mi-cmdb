from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ip_address import IPAddress
from app.models.nic import NIC
from app.schemas.ip_address import IPAddressCreate, IPAddressResponse

router = APIRouter(prefix="/api/v1/ip-addresses", tags=["ip-addresses"])


@router.get("", response_model=List[IPAddressResponse])
def list_ip_addresses(db: Session = Depends(get_db)):
    return db.query(IPAddress).filter(IPAddress.deleted_at.is_(None)).all()


@router.post("", response_model=IPAddressResponse, status_code=201)
def create_ip_address(data: IPAddressCreate, db: Session = Depends(get_db)):
    if not db.query(NIC).filter(NIC.id == data.nic_id).first():
        raise HTTPException(status_code=404, detail="NIC nicht gefunden")
    existing = db.query(IPAddress).filter(
        IPAddress.address == data.address,
        IPAddress.deleted_at.is_(None),
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="IP-Adresse bereits vergeben")
    ip = IPAddress(**data.model_dump())
    db.add(ip)
    db.commit()
    db.refresh(ip)
    return ip


@router.delete("/{ip_id}", status_code=204)
def delete_ip_address(ip_id: UUID, db: Session = Depends(get_db)):
    ip = db.query(IPAddress).filter(IPAddress.id == ip_id, IPAddress.deleted_at.is_(None)).first()
    if not ip:
        raise HTTPException(status_code=404, detail="IP-Adresse nicht gefunden")
    ip.deleted_at = datetime.utcnow()
    db.commit()
