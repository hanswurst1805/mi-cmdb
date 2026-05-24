from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.machine import Machine
from app.services.rag.chat import analyze_anomalies, chat
from app.services.rag.indexer import reindex_all
from app.services.rag.retriever import find_similar_machines, search_all

router = APIRouter(prefix="/api/v1", tags=["rag"])


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class ChatRequest(BaseModel):
    message: str


class SearchResultItem(BaseModel):
    type: str
    name: str
    score: float
    details: dict


class SearchResponse(BaseModel):
    results: List[SearchResultItem]


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


@router.post("/search", response_model=SearchResponse)
def semantic_search(req: SearchRequest, db: Session = Depends(get_db)):
    results = search_all(req.query, db, top_k=req.top_k)
    items = []
    for r in results:
        item = r["item"]
        if r["type"] == "machine":
            details = {
                "id": str(item.id),
                "fqdn": item.fqdn,
                "os": item.os,
                "ram_gb": item.ram_gb,
                "cpu_cores": item.cpu_cores,
                "status": item.status,
                "owner": item.owner,
            }
            name = item.fqdn
        else:
            details = {
                "id": str(item.id),
                "cidr": item.cidr,
                "gateway": item.gateway,
                "location": item.location,
            }
            name = item.name
        items.append(SearchResultItem(type=r["type"], name=name, score=r["score"], details=details))
    return SearchResponse(results=items)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest, db: Session = Depends(get_db)):
    result = chat(req.message, db)
    return ChatResponse(**result)


@router.get("/anomalies/{machine_id}")
def anomaly_detection(machine_id: UUID, db: Session = Depends(get_db)):
    machine = db.query(Machine).filter(Machine.id == machine_id, Machine.deleted_at.is_(None)).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden")
    similar = find_similar_machines(machine, db, top_k=10)
    analysis = analyze_anomalies(machine, similar)
    return {
        "machine": machine.fqdn,
        "similar_machines": [
            {"fqdn": s["machine"].fqdn, "score": s["score"]}
            for s in similar
        ],
        "analysis": analysis,
    }


@router.post("/reindex", status_code=200)
def trigger_reindex(db: Session = Depends(get_db)):
    result = reindex_all(db)
    return {"message": "Reindexierung abgeschlossen", **result}
