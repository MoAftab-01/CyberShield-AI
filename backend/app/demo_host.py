"""Demo-only same-origin hosting; the existing API keeps all authorization."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles

SPA_ROUTES = {
    "", "login", "register", "dashboard", "password", "url-scanner",
    "threat-intel", "reports", "settings", "copilot", "investigate",
}


def validate_demo_database(url, *, host_prefix, database, user):
    """Reject an unintended database before importing the application/schema."""
    normalized = "postgresql://" + url[len("postgres://"):] if url.startswith("postgres://") else url
    try:
        parsed = make_url(normalized)
        valid = (
            parsed.get_backend_name() == "postgresql"
            and bool(host_prefix) and parsed.host == host_prefix
            and parsed.database == database and bool(database)
            and parsed.username == user and bool(user)
        )
    except (ArgumentError, ValueError, TypeError, AttributeError):
        valid = False
    if not valid:
        raise ValueError("Demo database identity does not match the approved resource.")
    return normalized


def create_demo_app(api, frontend_directory):
    @asynccontextmanager
    async def lifespan(application):
        # Mounted FastAPI lifespans do not run automatically.
        async with api.router.lifespan_context(api):
            yield

    class ReactFiles(StaticFiles):
        async def get_response(self, path, scope):
            try:
                return await super().get_response(path, scope)
            except HTTPException as error:
                if error.status_code != 404 or path.strip("/") not in SPA_ROUTES:
                    raise
                return await super().get_response("index.html", scope)

    host = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    host.mount("/api", api)
    host.mount("/", ReactFiles(directory=Path(frontend_directory), html=True))
    return host
