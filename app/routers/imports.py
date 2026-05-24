"""
Import-Endpunkte für OCS Inventory und Lynis.

OCS Inventory
─────────────
Schickt Daten per POST an /api/v1/import/ocs.
Erwartet das Standard-JSON-Format der OCS-REST-API (v1).
Felder werden auf das Machine-Modell gemappt.
Neue Maschinen werden angelegt, bestehende (gleicher FQDN/Hostname) aktualisiert.

Lynis
─────
Schickt den Inhalt der lynis-report.dat per POST an /api/v1/import/lynis/{fqdn}.
Alternativ kann das geparste JSON-Format verwendet werden.
Ergebnisse werden in der security_audits-Tabelle gespeichert.
"""

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.machine import Machine
from app.models.security_audit import SecurityAudit
from app.services.rag.indexer import index_machine

router = APIRouter(prefix="/api/v1/import", tags=["imports"])


# ── OCS Inventory ────────────────────────────────────────────────────────────

class OCSNetwork(BaseModel):
    IPADDRESS: Optional[str] = None
    IPSUBNET: Optional[str] = None
    MACADDR: Optional[str] = None
    DESCRIPTION: Optional[str] = None


class OCSHardware(BaseModel):
    NAME: Optional[str] = None
    OSNAME: Optional[str] = None
    OSVERSION: Optional[str] = None
    MEMORY: Optional[int] = None       # MB
    PROCESSORN: Optional[int] = None   # Anzahl CPUs
    PROCESSORC: Optional[int] = None   # Kerne je CPU
    PROCESSORT: Optional[str] = None   # CPU-Typ
    IPADDR: Optional[str] = None
    DNS: Optional[str] = None
    WORKGROUP: Optional[str] = None


class OCSPayload(BaseModel):
    hardware: OCSHardware
    networks: Optional[List[OCSNetwork]] = []


@router.post("/ocs")
def import_ocs(
    payload: OCSPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    hw = payload.hardware
    hostname = hw.NAME or "unknown"
    fqdn = hostname if "." in hostname else f"{hostname}.local"
    os_str = " ".join(filter(None, [hw.OSNAME, hw.OSVERSION]))
    ram_gb = round(hw.MEMORY / 1024) if hw.MEMORY else None
    cpu_cores = (hw.PROCESSORN or 1) * (hw.PROCESSORC or 1) or None

    machine = db.query(Machine).filter(
        Machine.fqdn == fqdn, Machine.deleted_at.is_(None)
    ).first()

    created = False
    if machine is None:
        machine = Machine(fqdn=fqdn, hostname=hostname)
        db.add(machine)
        created = True

    machine.hostname = hostname
    if os_str:
        machine.os = os_str
    if ram_gb:
        machine.ram_gb = ram_gb
    if cpu_cores:
        machine.cpu_cores = cpu_cores
    machine.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(machine)
    background_tasks.add_task(index_machine, machine, db)

    return {
        "action": "created" if created else "updated",
        "machine_id": str(machine.id),
        "fqdn": machine.fqdn,
    }


# ── Lynis ─────────────────────────────────────────────────────────────────────

class LynisReportJSON(BaseModel):
    """Strukturiertes JSON-Format (empfohlen)."""
    hardening_index: Optional[int] = None
    lynis_version: Optional[str] = None
    warnings: Optional[List[str]] = []
    suggestions: Optional[List[str]] = []
    test_results: Optional[Dict[str, Any]] = {}
    audited_at: Optional[datetime] = None


def _parse_lynis_dat(content: str) -> dict:
    """Parst den Inhalt einer lynis-report.dat in ein strukturiertes Dict."""
    data: Dict[str, Any] = {"warnings": [], "suggestions": [], "test_results": {}}

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        if key == "hardening_index":
            try:
                data["hardening_index"] = int(value)
            except ValueError:
                pass
        elif key == "lynis_version":
            data["lynis_version"] = value
        elif key == "warning[]":
            data["warnings"].append(value)
        elif key == "suggestion[]":
            data["suggestions"].append(value)
        else:
            data["test_results"][key] = value

    return data


@router.post("/lynis/{fqdn}")
def import_lynis_json(
    fqdn: str,
    payload: LynisReportJSON,
    db: Session = Depends(get_db),
):
    machine = db.query(Machine).filter(
        Machine.fqdn == fqdn, Machine.deleted_at.is_(None)
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Maschine '{fqdn}' nicht gefunden")

    audit = SecurityAudit(
        machine_id=machine.id,
        hardening_index=payload.hardening_index,
        lynis_version=payload.lynis_version,
        warnings=payload.warnings or [],
        suggestions=payload.suggestions or [],
        test_results=payload.test_results or {},
        audited_at=payload.audited_at or datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "audit_id": str(audit.id),
        "machine": fqdn,
        "hardening_index": audit.hardening_index,
        "warnings": len(audit.warnings),
        "suggestions": len(audit.suggestions),
    }


@router.post("/lynis/{fqdn}/raw")
def import_lynis_raw(
    fqdn: str,
    body: Dict[str, str],
    db: Session = Depends(get_db),
):
    """Nimmt den Rohinhalt einer lynis-report.dat entgegen.
    Body: { "content": "<Inhalt der report.dat>" }
    """
    content = body.get("content", "")
    if not content:
        raise HTTPException(status_code=422, detail="'content' darf nicht leer sein")

    machine = db.query(Machine).filter(
        Machine.fqdn == fqdn, Machine.deleted_at.is_(None)
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Maschine '{fqdn}' nicht gefunden")

    data = _parse_lynis_dat(content)

    audit = SecurityAudit(
        machine_id=machine.id,
        hardening_index=data.get("hardening_index"),
        lynis_version=data.get("lynis_version"),
        warnings=data["warnings"],
        suggestions=data["suggestions"],
        test_results=data["test_results"],
        audited_at=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()
    db.refresh(audit)

    return {
        "audit_id": str(audit.id),
        "machine": fqdn,
        "hardening_index": audit.hardening_index,
        "warnings": len(audit.warnings),
        "suggestions": len(audit.suggestions),
    }


@router.get("/lynis/{fqdn}/audits")
def get_audits(fqdn: str, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(
        Machine.fqdn == fqdn, Machine.deleted_at.is_(None)
    ).first()
    if not machine:
        raise HTTPException(status_code=404, detail=f"Maschine '{fqdn}' nicht gefunden")

    audits = (
        db.query(SecurityAudit)
        .filter(SecurityAudit.machine_id == machine.id)
        .order_by(SecurityAudit.audited_at.desc())
        .all()
    )
    return [
        {
            "id": str(a.id),
            "hardening_index": a.hardening_index,
            "lynis_version": a.lynis_version,
            "warnings": len(a.warnings),
            "suggestions": len(a.suggestions),
            "audited_at": a.audited_at,
        }
        for a in audits
    ]
