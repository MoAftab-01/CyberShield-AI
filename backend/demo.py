"""Explicit demo entrypoint; app.main remains the normal runtime entrypoint."""
import os
from pathlib import Path

from sqlalchemy import create_engine, text

from app.demo_host import create_demo_app, validate_demo_database

os.environ["DATABASE_URL"] = validate_demo_database(
    os.environ["DATABASE_URL"],
    host_prefix=os.environ["DEMO_DATABASE_HOST_PREFIX"],
    database=os.environ["DEMO_DATABASE_NAME"],
    user=os.environ["DEMO_DATABASE_USER"],
)

# Verify the actual connection before app.main can initialize its schema.
probe = create_engine(os.environ["DATABASE_URL"])
try:
    with probe.connect() as connection:
        identity = connection.execute(text("SELECT current_database(), current_user")).one()
        if tuple(identity) != (os.environ["DEMO_DATABASE_NAME"], os.environ["DEMO_DATABASE_USER"]):
            raise ValueError("Unintended database")
        tables = connection.execute(text(
            "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
        )).scalar_one()
    print(f"[demo] isolated database identity verified; existing public tables: {tables}")
except Exception:
    raise RuntimeError("Demo database verification unavailable.") from None
finally:
    probe.dispose()

from app.main import app as api  # noqa: E402

app = create_demo_app(api, Path(__file__).resolve().parent / "frontend_dist")
