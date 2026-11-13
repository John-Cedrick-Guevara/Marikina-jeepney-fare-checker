import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Local development reads back-end/.env; on Vercel the variables come from the project settings
try:
    from dotenv import load_dotenv  # installed with pydantic-settings
    load_dotenv()
except ImportError:
    pass

# Get connection string from environment variable
# Without one, use the local database from `supabase db start` (tests); engines connect lazily,
# so importing the app never fails
SUPABASE_CONNECTION_STRING = os.getenv(
    "SUPABASE_CONNECTION_STRING", "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
)
# On Vercel a missing variable is a misconfiguration: fail loudly instead of trying localhost
if os.getenv("VERCEL") and not os.getenv("SUPABASE_CONNECTION_STRING"):
    raise ValueError("SUPABASE_CONNECTION_STRING environment variable is not set")

# Convert postgresql:// to postgresql+psycopg2:// to use psycopg2-binary
connection_string = SUPABASE_CONNECTION_STRING
if connection_string.startswith("postgresql://"):
    connection_string = connection_string.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(
    connection_string,
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

