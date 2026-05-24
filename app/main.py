from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import auth, ip_addresses, machines, networks, rag, ui

app = FastAPI(
    title="Mini-CMDB",
    description="Leichtgewichtige Configuration Management Database mit RAG",
    version="1.0.0",
)

app.include_router(machines.router)
app.include_router(networks.router)
app.include_router(ip_addresses.router)
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(ui.router)
