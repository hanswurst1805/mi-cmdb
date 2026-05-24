import ipaddress
from datetime import datetime
from typing import List
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ip_address import IPAddress
from app.models.network import Network
from app.schemas.ip_address import IPAddressResponse
from app.schemas.network import NetworkCreate, NetworkResponse, NetworkUpdate
from app.services.rag.indexer import index_network

router = APIRouter(prefix="/api/v1/networks", tags=["networks"])


def _get_or_404(network_id: UUID, db: Session) -> Network:
    n = db.query(Network).filter(Network.id == network_id).first()
    if not n:
        raise HTTPException(status_code=404, detail="Netzwerk nicht gefunden")
    return n


@router.get("", response_model=List[NetworkResponse])
def list_networks(db: Session = Depends(get_db)):
    return db.query(Network).order_by(Network.name).all()


@router.post("", response_model=NetworkResponse, status_code=201)
def create_network(data: NetworkCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        ipaddress.ip_network(data.cidr, strict=False)
    except ValueError:
        raise HTTPException(status_code=422, detail="Ungültiges CIDR-Format")
    if db.query(Network).filter(Network.cidr == data.cidr).first():
        raise HTTPException(status_code=409, detail="CIDR bereits vorhanden")
    network = Network(**data.model_dump())
    db.add(network)
    db.commit()
    db.refresh(network)
    background_tasks.add_task(index_network, network, db)
    return network


@router.get("/{network_id}", response_model=NetworkResponse)
def get_network(network_id: UUID, db: Session = Depends(get_db)):
    return _get_or_404(network_id, db)


@router.put("/{network_id}", response_model=NetworkResponse)
def update_network(
    network_id: UUID, data: NetworkUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    network = _get_or_404(network_id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(network, field, value)
    network.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(network)
    background_tasks.add_task(index_network, network, db)
    return network


@router.get("/{network_id}/ips", response_model=List[IPAddressResponse])
def get_network_ips(network_id: UUID, db: Session = Depends(get_db)):
    _get_or_404(network_id, db)
    return db.query(IPAddress).filter(
        IPAddress.network_id == network_id,
        IPAddress.deleted_at.is_(None),
    ).all()


@router.get("/{network_id}/free")
def get_free_ips(network_id: UUID, limit: int = 20, db: Session = Depends(get_db)):
    network = _get_or_404(network_id, db)
    try:
        net = ipaddress.ip_network(network.cidr, strict=False)
    except ValueError:
        raise HTTPException(status_code=422, detail="Ungültiges CIDR im Netzwerk")

    used = {
        row.address
        for row in db.query(IPAddress.address).filter(
            IPAddress.network_id == network_id,
            IPAddress.deleted_at.is_(None),
        )
    }
    free = []
    for host in net.hosts():
        if str(host) not in used:
            free.append(str(host))
        if len(free) >= limit:
            break
    return {"network": network.cidr, "free_ips": free, "total_shown": len(free)}
