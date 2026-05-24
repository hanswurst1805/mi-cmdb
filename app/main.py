from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.routers import auth, imports, ip_addresses, login, machines, networks, rag, ui

app = FastAPI(
    title="Mini-CMDB",
    description="Leichtgewichtige Configuration Management Database mit RAG",
    version="1.0.0",
)

@app.middleware("http")
async def require_login(request: Request, call_next):
    public_paths = {"/login", "/docs", "/openapi.json", "/redoc"}
    if request.url.path in public_paths or request.url.path.startswith("/api/"):
        return await call_next(request)
    if not request.session.get("authenticated"):
        return RedirectResponse(url="/login", status_code=302)
    return await call_next(request)


# SessionMiddleware muss nach require_login registriert werden,
# damit sie beim Request zuerst läuft und request.session befüllt
app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)

app.include_router(login.router)
app.include_router(imports.router)
app.include_router(machines.router)
app.include_router(networks.router)
app.include_router(ip_addresses.router)
app.include_router(auth.router)
app.include_router(rag.router)
app.include_router(ui.router)
