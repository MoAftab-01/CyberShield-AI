"""Isolated browser-test server. Never import the live app or use real storage."""
import argparse
from datetime import datetime, timezone
import hashlib
import inspect
import json
import os
from pathlib import Path
import socket
import sys

args = argparse.ArgumentParser()
args.add_argument("--data", required=True)
args.add_argument("--assets", required=True)
args.add_argument("--backend", required=True)
args.add_argument("--port", required=True, type=int)
args.add_argument("--legacy", action="store_true")
args.add_argument("--production-ui", action="store_true")
options = args.parse_args()
data = Path(options.data).resolve()
assets = Path(options.assets).resolve()
backend = Path(options.backend).resolve()
assert backend == Path(__file__).resolve().parents[3] / "backend"
assert data.is_dir() and not data.is_relative_to(backend.parent)
assert assets.is_relative_to(data.parent)
assert not (backend / ".env").exists(), "Test server refuses a worktree dotenv file."
for name in ("vector_db", "uploads", "knowledge_base"):
    (data / name).mkdir(exist_ok=True)
os.chdir(data)
os.environ.update(ENVIRONMENT="test", DATABASE_URL="sqlite:///" + str(data / "browser.db"),
    JWT_SECRET="isolated-browser-signing-fixture-value-only",
    JWT_ALGORITHM="HS256", GROQ_API_KEY="synthetic-unused", OPENAI_API_KEY="synthetic-unused",
    VT_API_KEY="", EMBEDDING_BACKEND="hash", VECTOR_DB_DIR=str(data / "vector_db"),
    CYBERGPT_V2_ENABLED="false" if options.legacy else "true",
    CVE_INVESTIGATION_ENABLED="true", CVE_INVESTIGATION_LIVE_APPROVED="false")
sys.path.insert(0, str(backend))
blocked = []
(data / "isolation.json").write_text(json.dumps({"blocked": blocked}), encoding="utf-8")
connect = socket.socket.connect
def guarded_connect(sock, address):
    if (isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"} and
        any(frame.function in {"socketpair", "_fallback_socketpair"} and
            Path(frame.filename).resolve() == Path(socket.__file__).resolve()
            for frame in inspect.stack(context=0))):
        return connect(sock, address)
    blocked.append("socket")
    (data / "isolation.json").write_text(json.dumps({"blocked": blocked}), encoding="utf-8")
    raise RuntimeError("Test server outbound connection forbidden")
socket.socket.connect = guarded_connect
socket.socket.connect_ex = guarded_connect
import psycopg2
def deny_postgres(*a, **k):
    blocked.append("postgres")
    (data / "isolation.json").write_text(json.dumps({"blocked": blocked}), encoding="utf-8")
    raise RuntimeError("PostgreSQL forbidden in browser tests")
psycopg2.connect = deny_postgres

from app.database.init_db import init_db
from app.database.database import SessionLocal
from app.database.models import User
from app.core.security import hash_password
init_db()
session = SessionLocal()
users = []
for label in ("alpha", "beta"):
    user = User(name=label, email=label+"@example.com", hashed_password=hash_password("SyntheticBrowserPass923!"))
    session.add(user)
    session.commit()
    session.refresh(user)
    users.append(user.id)
session.close()
date = "2026-11-10T00:00:00Z"
public = {"records": [{"record_id": "JUNIPER", "title": "Juniper recovery",
    "modified_at": date, "published_at": "2026-01-02T00:00:00Z",
    "sections": [{"heading": "Recovery", "text": "Juniper TLS recovery requires two independent operator approvals."},
                 {"heading": "Records", "text": "Juniper TLS recovery records approvals from both independent operators."}]}]}
(data / "public.json").write_text(json.dumps(public), encoding="utf-8")
private = "Amber gateway recovery requires two operators."
(data / "private.txt").write_text(private, encoding="utf-8")
artifacts = [
    {"artifact_id": "public", "filename": "public.json", "source_id": "fixture-reference",
     "adapter": "reference-fixture", "trust": "synthetic_fixture", "retrieved_at": date,
     "sha256": hashlib.sha256((data / "public.json").read_bytes()).hexdigest()},
    {"artifact_id": "private", "filename": "private.txt", "source_id": "private-upload",
     "adapter": "private-text", "trust": "private_upload", "retrieved_at": date,
     "record_id": "AMBER", "title": "Amber recovery", "owner_id": users[0],
     "sha256": hashlib.sha256((data / "private.txt").read_bytes()).hexdigest()}]
manifest = data / "manifest.json"
manifest.write_text(json.dumps({"format_version": 1, "artifacts": artifacts}), encoding="utf-8")
os.environ["CYBERGPT_V2_CATALOG_MANIFEST"] = str(manifest)
from app.core.config import settings
settings.CYBERGPT_V2_CATALOG_MANIFEST = manifest
from app.services.llm.provider_factory import ProviderFactory
class Provider:
    def chat(self, prompt, **kwargs):
        return "Legacy synthetic answer."
    def chat_bounded(self, prompt, **kwargs):
        payload = json.loads(prompt.rsplit("\n", 1)[1])
        if "timeout" in payload["question"].lower():
            raise TimeoutError("Synthetic provider timeout")
        return json.dumps({"claims": [{"text": e["excerpt"], "citation_ids": [e["citation_id"]]}
                                     for e in payload["evidence"]]})
ProviderFactory._provider = Provider()
from app.services.password_service import PasswordService
PasswordService.generate_secure = staticmethod(lambda length: {
    "password": "SYNTHETIC_UI#Value923!", "length": 22, "score": 5, "strength": "Strong",
    "entropy": 90.0, "entropy_rating": "High"})
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.api import copilot_routes, conversation_routes, user_routes, upload_routes

app = FastAPI()
from app.api.investigation_routes import router as investigation_router
app.include_router(investigation_router, prefix="/api")
for router in (copilot_routes.router, conversation_routes.router, user_routes.router, upload_routes.router):
    app.include_router(router, prefix="/api")
@app.get("/health")
def health():
    return {"isolated": True}
@app.get("/login")
def login_page():
    return FileResponse(assets / "index.html") if options.production_ui else HTMLResponse("<h1>Login required</h1>")
app.mount("/assets", StaticFiles(directory=assets / "assets" if (assets / "assets").is_dir() else assets), name="assets")
@app.get("/{path:path}")
def frontend_page(path: str):
    return FileResponse(assets / "index.html")
(data / "ready.json").write_text(json.dumps({"users": users, "legacy": options.legacy}), encoding="utf-8")
import uvicorn
try:
    uvicorn.run(app, host="127.0.0.1", port=options.port, access_log=False, log_level="error")
finally:
    (data / "isolation.json").write_text(json.dumps({"blocked": blocked}), encoding="utf-8")
