"""Validate migrations/API/startup in a NEW native PostgreSQL cluster only.

Run from any cwd: python -B backend/validation/disposable_postgres.py
Never reads DATABASE_URL or connects to an existing cluster. Leaves stopped
synthetic storage for review; deletes its one temporary password file.
"""
from pathlib import Path
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time


def main():
    root = Path(__file__).resolve().parents[2]
    scratch = Path(tempfile.mkdtemp(prefix="cybershield-launch-pg-")).resolve()
    data = scratch / "cluster"
    marker = scratch / "CREATED_BY_CYBERSHIELD_VALIDATION"
    marker.write_text(secrets.token_hex(32))
    role, password = "launch_" + secrets.token_hex(5), secrets.token_urlsafe(32)
    pwfile = scratch / "init-password"
    pwfile.write_text(password + "\n")
    pgctl, initdb = shutil.which("pg_ctl"), shutil.which("initdb")
    if not pgctl or not initdb:
        raise RuntimeError("Native PostgreSQL binaries are required; no fallback to existing databases.")
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = {k: v for k, v in os.environ.items() if not k.startswith("PG")}
    checks = []
    started = False

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def run(args):
        with (scratch / "tools.log").open("ab") as output:
            result = subprocess.run(args, env=env, cwd=scratch, stdout=output, stderr=output,
                                    timeout=60, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if result.returncode:
            # Tool output can contain private local paths: retain it, don't echo.
            pass  # Output is already captured in the private tools.log.
            raise RuntimeError("Disposable PostgreSQL tool failed. See private artifact log.")

    try:
        run([initdb, "-D", str(data), "-U", role, "--pwfile", str(pwfile),
             "--auth=scram-sha-256", "--no-locale", "--encoding=UTF8"])
        pwfile.unlink()
        run([pgctl, "-D", str(data), "-l", str(scratch / "postgres.log"),
             "-o", "-h 127.0.0.1 -p " + str(port), "-w", "start"])
        started = True
        pid = (data / "postmaster.pid").read_text().splitlines()
        check("process_data_directory_guard", Path(pid[1]).resolve() == data)
        check("process_port_guard", int(pid[3]) == port)
        import psycopg2
        from psycopg2 import sql

        def connect(database):
            conn = psycopg2.connect(host="127.0.0.1", port=port, user=role,
                password=password, dbname=database, connect_timeout=3)
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute("SELECT current_setting('data_directory'), inet_server_port(), current_user")
                directory, actual_port, actual_role = cursor.fetchone()
                check("connection_identity_" + database,
                      Path(directory).resolve() == data and actual_port == port and actual_role == role)
            return conn

        admin = connect("postgres")
        with admin.cursor() as cursor:
            cursor.execute("CREATE DATABASE launch_validation")
        admin.close()
        conn = connect("launch_validation")
        with conn.cursor() as cursor:
            cursor.execute("COMMENT ON DATABASE launch_validation IS 'isolated-synthetic-launch-validation'")
            cursor.execute("SELECT shobj_description(oid,'pg_database') FROM pg_database WHERE datname=current_database()")
            check("database_marker_guard", cursor.fetchone()[0] == "isolated-synthetic-launch-validation")

        # Explicit synthetic settings before application imports. No .env exists
        # in the isolated feature worktree. All local file storage is temporary.
        check("no_worktree_dotenv", not (root / "backend/.env").exists())
        os.chdir(scratch)
        for name in ("vector_db", "knowledge_base", "uploads"):
            (scratch / name).mkdir()
        os.environ.update(ENVIRONMENT="test",
            DATABASE_URL="postgresql+psycopg2://" + role + ":" + password
                + "@127.0.0.1:" + str(port) + "/launch_validation",
            JWT_SECRET=secrets.token_urlsafe(48), EMBEDDING_BACKEND="hash",
            VECTOR_DB_DIR=str(scratch / "vector_db"), GROQ_API_KEY="synthetic-unused",
            OPENAI_API_KEY="synthetic-unused", VT_API_KEY="",
            CYBERGPT_V2_ENABLED="false", CVE_INVESTIGATION_ENABLED="true",
            CVE_INVESTIGATION_LIVE_APPROVED="false", LANGSMITH_TRACING="false",
            LANGCHAIN_TRACING_V2="false")
        os.environ.pop("CYBERGPT_V2_CATALOG_MANIFEST", None)
        sys.path.insert(0, str(root / "backend"))
        # Block non-local sockets after the verified cluster is established.
        original_connect = socket.socket.connect
        def guarded_connect(sock, address):
            if isinstance(address, tuple) and address[0] in {"127.0.0.1", "::1"}:
                return original_connect(sock, address)
            raise AssertionError("Non-local network forbidden in PostgreSQL validation")
        socket.socket.connect = guarded_connect

        from app.database.init_db import init_db
        from app.database.database import Base, SessionLocal, engine
        init_db()
        with conn.cursor() as cursor:
            cursor.execute("ALTER TABLE threat_searches DROP COLUMN user_id")
            cursor.execute("INSERT INTO threat_searches (cve,severity,risk_level,known_exploited,searched_at) VALUES ('CVE-2099-9999','HIGH','HIGH',false,CURRENT_TIMESTAMP)")
            migration = (root / "backend/migrations/001_threat_search_ownership.sql").read_text()
            cursor.execute(migration)
            cursor.execute("SELECT user_id FROM threat_searches")
            check("legacy_null_preserved", cursor.fetchall() == [(None,)])
            cursor.execute("SELECT indexname FROM pg_indexes WHERE tablename='threat_searches'")
            check("ownership_index", "ix_threat_searches_user_id" in {r[0] for r in cursor.fetchall()})
            cursor.execute("SELECT confdeltype FROM pg_constraint WHERE conname='fk_threat_searches_user_id'")
            check("foreign_key_delete_set_null", cursor.fetchone() == ("n",))
            try:
                cursor.execute(migration)
            except psycopg2.errors.DuplicateColumn:
                cursor.execute("ROLLBACK")
            else:
                raise AssertionError("Expected single-use migration to reject duplicate application")
            cursor.execute("SELECT count(*) FROM threat_searches")
            check("single_use_failure_preserves_data", cursor.fetchone()[0] == 1)
            # Force a mid-migration FK failure, prove ADD COLUMN rolls back.
            cursor.execute("CREATE SCHEMA failure_check")
            cursor.execute("CREATE TABLE failure_check.threat_searches (id integer)")
            cursor.execute("SET search_path TO failure_check")
            try:
                cursor.execute(migration)
            except psycopg2.errors.UndefinedTable:
                cursor.execute("ROLLBACK")
            else:
                raise AssertionError("Expected missing users table to reject migration")
            cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='failure_check'")
            check("migration_failure_is_atomic", cursor.fetchall() == [("id",)])
            cursor.execute("SET search_path TO public")

        from sqlalchemy import inspect
        from app.models.threat_search import ThreatSearch
        columns = {c["name"]: c for c in inspect(engine).get_columns("threat_searches")}
        check("orm_columns_match", set(columns) == set(ThreatSearch.__table__.columns.keys()))
        check("owner_nullable_matches", columns["user_id"]["nullable"])
        from app.database.models import User
        from app.core.security import hash_password, create_access_token
        from app.database.threat_crud import ThreatCRUD
        session = SessionLocal()
        users = []
        for label in ("alpha", "beta"):
            user = User(name=label, email=label + "@example.com",
                        hashed_password=hash_password("SyntheticOnly-PG923!"))
            session.add(user)
            session.commit()
            session.refresh(user)
            users.append(user)
        for user in users:
            ThreatCRUD.save_search(session, {
                "cve": "CVE-2021-44228", "severity": "HIGH", "risk_level": "HIGH",
                "cvss": 8.1, "known_exploited": True}, user_id=user.id)
        for user in users:
            rows = ThreatCRUD.get_recent_searches(session, user_id=user.id)
            check("crud_owner_" + str(user.id), len(rows) == 1 and rows[0].user_id == user.id)
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.api import threat_routes, investigation_routes
        from app.database.database import get_db
        app = FastAPI()
        app.include_router(threat_routes.router)
        app.include_router(investigation_routes.router)
        app.dependency_overrides[get_db] = lambda: session
        with TestClient(app) as client:
            check("unauthenticated_history_denied", client.get("/threats/history").status_code in {401,403})
            for user in users:
                headers = {"Authorization": "Bearer " + create_access_token({"sub": user.email})}
                response = client.get("/threats/history", headers=headers)
                check("api_owner_history_" + str(user.id),
                      response.status_code == 200 and len(response.json()) == 1)
                check("api_owner_stats_" + str(user.id),
                      client.get("/threats/stats", headers=headers).json()["total_searches"] == 1)
                result = client.post("/investigations/cve", headers=headers,
                                     json={"cve": "CVE-2021-44228"})
                check("postgres_authenticated_graph_" + str(user.id),
                      result.status_code == 200 and result.json()["status"] == "complete")
        # Database-enforced FK rejection; no guessed or non-existent owners.
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO threat_searches (cve,severity,risk_level,known_exploited,searched_at,user_id) VALUES ('CVE-2099-8888','HIGH','HIGH',false,CURRENT_TIMESTAMP,999999)")
            except psycopg2.errors.ForeignKeyViolation:
                check("foreign_owner_rejected", True)
            else:
                raise AssertionError("Missing ownership FK enforcement")
        # Exercise an actual concurrent unique-email race in this disposable PG.
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from app.services import user_service
        from app.schemas.user_schema import UserCreate
        barrier = Barrier(2)
        original_hash = user_service.hash_password
        def synchronized_hash(value):
            encoded = original_hash(value)
            barrier.wait(timeout=10)
            return encoded
        user_service.hash_password = synchronized_hash
        def register_race():
            race_session = SessionLocal()
            try:
                user_service.UserService.create_user(race_session, UserCreate(
                    name="Synthetic Race", email="race@example.com", password="SyntheticRaceOnly923!"))
                return "created"
            except ValueError as error:
                return "duplicate" if str(error) == "Email already exists." else "unexpected"
            finally:
                race_session.close()
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures = [pool.submit(register_race) for _ in range(2)]
                check("concurrent_registration_unique_and_controlled", sorted(f.result(timeout=20) for f in futures) == ["created", "duplicate"])
        finally:
            user_service.hash_password = original_hash
        # Actual FastAPI startup; stub only corpus preparation, not auth or DB.
        from app import main as application
        application._prepare_knowledge_base = lambda: None
        with TestClient(application.app) as client:
            check("actual_startup_health", client.get("/health").status_code == 200)
            check("actual_startup_readiness", client.get("/ready").status_code == 200)
        session.close()
        engine.dispose()
        conn.close()
        report = {"passed": len(checks), "failed": 0, "checks": checks,
                  "postgres_major": 18, "native_disposable_cluster": True,
                  "migration": "001_threat_search_ownership.sql (intentionally single-use)",
                  "application_data_accessed": False}
        (scratch / "results.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report))
    finally:
        if pwfile.exists():
            pwfile.unlink()
        if started:
            # Never address another cluster; verify our absolute path and marker.
            assert marker.is_file() and data.parent == scratch
            assert scratch.name.startswith("cybershield-launch-pg-")
            run([pgctl, "-D", str(data), "-m", "fast", "-w", "stop"])
        print("Disposable cluster stopped; synthetic artifacts: " + str(scratch))


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        # No SQLAlchemy URLs, credentials or token-bearing requests in diagnostics.
        print("POSTGRES_VALIDATION_FAILED: " + type(error).__name__)
        raise SystemExit(1)
