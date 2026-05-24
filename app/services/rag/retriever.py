from typing import List

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.machine import Machine
from app.models.network import Network
from app.services.rag.embeddings import embed_query


def search_machines(query: str, db: Session, top_k: int = 5) -> List[dict]:
    q_vec = embed_query(query)
    results = (
        db.query(Machine, Machine.embedding.cosine_distance(q_vec).label("distance"))
        .filter(Machine.deleted_at.is_(None), Machine.embedding.isnot(None))
        .order_by("distance")
        .limit(top_k)
        .all()
    )
    return [
        {"type": "machine", "score": round(1 - r.distance, 4), "item": r.Machine}
        for r in results
    ]


def search_networks(query: str, db: Session, top_k: int = 5) -> List[dict]:
    q_vec = embed_query(query)
    results = (
        db.query(Network, Network.embedding.cosine_distance(q_vec).label("distance"))
        .filter(Network.embedding.isnot(None))
        .order_by("distance")
        .limit(top_k)
        .all()
    )
    return [
        {"type": "network", "score": round(1 - r.distance, 4), "item": r.Network}
        for r in results
    ]


def search_all(query: str, db: Session, top_k: int = 5) -> List[dict]:
    machines = search_machines(query, db, top_k)
    networks = search_networks(query, db, top_k)
    combined = machines + networks
    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:top_k]


def find_similar_machines(machine: Machine, db: Session, top_k: int = 10) -> List[dict]:
    if machine.embedding is None:
        return []
    results = (
        db.query(Machine, Machine.embedding.cosine_distance(machine.embedding).label("distance"))
        .filter(Machine.id != machine.id, Machine.deleted_at.is_(None), Machine.embedding.isnot(None))
        .order_by("distance")
        .limit(top_k)
        .all()
    )
    return [
        {"score": round(1 - r.distance, 4), "machine": r.Machine}
        for r in results
    ]
