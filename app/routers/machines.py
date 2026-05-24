from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.machine import Machine, MachineStatus
from app.schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from app.schemas.nic import NICResponse
from app.services.rag.indexer import index_machine

router = APIRouter(prefix="/api/v1/machines", tags=["machines"])


def _get_or_404(machine_id: UUID, db: Session) -> Machine:
    m = db.query(Machine).filter(Machine.id == machine_id, Machine.deleted_at.is_(None)).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden")
    return m


@router.get("", response_model=List[MachineResponse])
def list_machines(
    status: Optional[MachineStatus] = None,
    os: Optional[str] = Query(None),
    owner: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    q = db.query(Machine).filter(Machine.deleted_at.is_(None))
    if status:
        q = q.filter(Machine.status == status)
    if os:
        q = q.filter(Machine.os.ilike(f"%{os}%"))
    if owner:
        q = q.filter(Machine.owner.ilike(f"%{owner}%"))
    return q.order_by(Machine.fqdn).all()


@router.post("", response_model=MachineResponse, status_code=201)
def create_machine(data: MachineCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if db.query(Machine).filter(Machine.fqdn == data.fqdn, Machine.deleted_at.is_(None)).first():
        raise HTTPException(status_code=409, detail="FQDN bereits vorhanden")
    machine = Machine(**data.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    background_tasks.add_task(index_machine, machine, db)
    return machine


@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(machine_id: UUID, db: Session = Depends(get_db)):
    return _get_or_404(machine_id, db)


@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: UUID, data: MachineUpdate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)
):
    machine = _get_or_404(machine_id, db)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(machine, field, value)
    machine.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(machine)
    background_tasks.add_task(index_machine, machine, db)
    return machine


@router.delete("/{machine_id}", status_code=204)
def delete_machine(machine_id: UUID, db: Session = Depends(get_db)):
    machine = _get_or_404(machine_id, db)
    machine.deleted_at = datetime.utcnow()
    db.commit()


@router.get("/{machine_id}/nics", response_model=List[NICResponse])
def get_machine_nics(machine_id: UUID, db: Session = Depends(get_db)):
    machine = _get_or_404(machine_id, db)
    return machine.nics
