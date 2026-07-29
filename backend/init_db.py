from app.database.database import Base, engine

# Import all models so SQLAlchemy knows about them
from app.database.models import User

print("Creating database tables...")

Base.metadata.create_all(bind=engine)

print("Database initialized successfully!")