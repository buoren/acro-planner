import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

load_dotenv()

# Database configuration - ready for Google Cloud SQL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://user:password@localhost/acro_planner"
)

# For Google Cloud SQL, the connection string will be:
# mysql+pymysql://user:password@/database_name?unix_socket=/cloudsql/project:region:instance

# SQLite (used in tests) doesn't support pool_size and max_overflow
is_sqlite = DATABASE_URL.startswith("sqlite")
engine_kwargs = {
    "pool_pre_ping": True,  # Verify connections before using them
}

if not is_sqlite:
    # MySQL-specific pool settings
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
    })
else:
    # SQLite-specific settings
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
