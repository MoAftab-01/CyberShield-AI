from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    pass


#: SQLite needs one extra argument to be usable from FastAPI.
#:
#: Synchronous endpoints run in a worker thread pool, so the connection that
#: created the session and the thread that uses it are not always the same.
#: SQLite refuses that by default, which shows up as an intermittent
#: "objects created in a thread can only be used in that same thread" rather
#: than as a clean error at startup. Postgres has no such restriction, so the
#: argument is only added for SQLite - this is what makes a SQLite
#: DATABASE_URL a working local-development option instead of a trap.
_CONNECT_ARGS = (
    {"check_same_thread": False}
    if settings.DATABASE_URL.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    connect_args=_CONNECT_ARGS,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
    
def get_db():
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()