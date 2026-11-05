import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Get connection string from environment variable
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")

if not SUPABASE_CONNECTION_STRING:
    raise ValueError("SUPABASE_CONNECTION_STRING environment variable is not set")

engine = create_engine(
    SUPABASE_CONNECTION_STRING,
    pool_pre_ping=True,  # Verify connections before using them
    pool_recycle=300,    # Recycle connections after 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

