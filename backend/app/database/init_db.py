from app.database.database import Base, engine

# Database Models
from app.database.models import User

# Feature Models
from app.models.password_scan import PasswordScan
from app.models.url_scan import URLScan
from app.models.threat_search import ThreatSearch

# Conversation Models
from app.models.conversation import Conversation
from app.models.chat_message import ChatMessage


def init_db():
    Base.metadata.create_all(bind=engine)