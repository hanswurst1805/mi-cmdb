from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.ip_address import IPAddress
from app.models.machine import Machine, MachineStatus
from app.models.network import Network
from app.services.rag.retriever import find_similar_machines

router = APIRouter(tags=["ui"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    machines = db.query(Machine).filter(Machine.deleted_at.is_(None)).all()
    stats = {
        "machines": len(machines),
        "active": sum(1 for m in machines if m.status == MachineStatus.active),
        "inactive": sum(1 for m in machines if m.status == MachineStatus.inactive),
        "decommissioned": sum(1 for m in machines if m.status == MachineStatus.decommissioned),
        "networks": db.query(Network).count(),
        "ips": db.query(IPAddress).filter(IPAddress.deleted_at.is_(None)).count(),
    }
    recent_machines = sorted(machines, key=lambda m: m.created_at, reverse=True)[:5]
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "stats": stats, "recent_machines": recent_machines
    })


@router.get("/machines", response_class=HTMLResponse)
def machines_list(
    request: Request,
    status: Optional[str] = None,
    os: Optional[str] = None,
    owner: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(Machine).filter(Machine.deleted_at.is_(None))
    if status:
        q = q.filter(Machine.status == status)
    if os:
        q = q.filter(Machine.os.ilike(f"%{os}%"))
    if owner:
        q = q.filter(Machine.owner.ilike(f"%{owner}%"))
    machines = q.order_by(Machine.fqdn).all()
    return templates.TemplateResponse("machines/list.html", {
        "request": request,
        "machines": machines,
        "filter_status": status,
        "filter_os": os,
        "filter_owner": owner,
    })


@router.post("/machines")
async def machines_create(
    request: Request,
    fqdn: str = Form(...),
    hostname: str = Form(...),
    os: Optional[str] = Form(None),
    ram_gb: Optional[int] = Form(None),
    cpu_cores: Optional[int] = Form(None),
    owner: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    machine = Machine(
        fqdn=fqdn, hostname=hostname, os=os or None,
        ram_gb=ram_gb, cpu_cores=cpu_cores,
        owner=owner or None, description=description or None,
    )
    db.add(machine)
    db.commit()
    return RedirectResponse(url=f"/machines/{machine.id}", status_code=303)


@router.get("/machines/{machine_id}", response_class=HTMLResponse)
def machine_detail(request: Request, machine_id: UUID, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id, Machine.deleted_at.is_(None)).first()
    if not machine:
        return RedirectResponse("/machines")
    similar = find_similar_machines(machine, db, top_k=5) if machine.embedding is not None else []
    return templates.TemplateResponse("machines/detail.html", {
        "request": request, "machine": machine, "similar": similar
    })


@router.get("/networks", response_class=HTMLResponse)
def networks_list(request: Request, db: Session = Depends(get_db)):
    networks = db.query(Network).order_by(Network.name).all()
    network_data = []
    for n in networks:
        ip_count = db.query(IPAddress).filter(
            IPAddress.network_id == n.id, IPAddress.deleted_at.is_(None)
        ).count()
        network_data.append({"id": n.id, "name": n.name, "cidr": n.cidr,
                              "gateway": n.gateway, "location": n.location, "ip_count": ip_count})
    return templates.TemplateResponse("networks/list.html", {
        "request": request, "networks": network_data
    })


@router.post("/networks")
async def networks_create(
    name: str = Form(...),
    cidr: str = Form(...),
    gateway: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    network = Network(name=name, cidr=cidr, gateway=gateway or None,
                      location=location or None, description=description or None)
    db.add(network)
    db.commit()
    return RedirectResponse(url="/networks", status_code=303)


@router.get("/chat", response_class=HTMLResponse)
def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
