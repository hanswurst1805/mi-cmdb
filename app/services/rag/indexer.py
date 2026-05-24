from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.network import Network
from app.services.rag.embeddings import embed_text


def index_machine(machine: Machine, db: Session) -> None:
    if not machine.fqdn:
        return
    machine.embedding = embed_text(machine.to_text())
    db.add(machine)
    db.commit()


def index_network(network: Network, db: Session) -> None:
    if not network.name:
        return
    network.embedding = embed_text(network.to_text())
    db.add(network)
    db.commit()


def reindex_all(db: Session) -> dict:
    machines = db.query(Machine).filter(Machine.deleted_at.is_(None)).all()
    networks = db.query(Network).all()

    for m in machines:
        m.embedding = embed_text(m.to_text())
    for n in networks:
        n.embedding = embed_text(n.to_text())

    db.commit()
    return {"machines": len(machines), "networks": len(networks)}
