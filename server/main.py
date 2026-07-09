from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from server.config import settings
from server.db import init_db, SessionLocal
from server.models import Client, SettingsKV


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    # Seed server schema version if absent
    with SessionLocal() as db:
        sv = db.get(SettingsKV, "server_schema_version")
        if not sv:
            sv = SettingsKV(key="server_schema_version", value=str(settings.SERVER_SCHEMA_VERSION))
            db.add(sv)
            db.commit()
    yield


app = FastAPI(title="OpsCollector Sync Server", lifespan=lifespan)
init_db()


@app.get("/api/v1/health")
def health():
    db_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "db": "ok" if db_ok else "error", "timestamp": __import__("datetime").datetime.now().isoformat()}


@app.post("/api/v1/register")
def register(payload: dict | None = None):
    payload = payload or {}
    cid = payload.get("client_id") or __import__("secrets").token_hex(16)
    from server.auth import issue_token
    token = issue_token(cid, payload.get("client_name"))
    created = True
    with SessionLocal() as db:
        existing = db.get(Client, cid)
        created = existing is None
    return {"client_id": cid, "api_token": token, "created": created}


from server.routers.sync import router as sync_router

app.include_router(sync_router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host="127.0.0.1", port=8000, reload=False)
