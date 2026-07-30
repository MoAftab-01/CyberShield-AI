from app.database.database import Base, engine

from app.database.models import User

from app.models.password_scan import PasswordScan
from app.models.url_scan import URLScan
from app.models.threat_search import ThreatSearch


def init_db():
    Base.metadata.create_all(bind=engine)