"""
SQLAlchemy models for Acro Planner application.

This file contains example models to demonstrate the structure.
Replace with your actual models as needed.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, Numeric, JSON, TypeDecorator, CHAR
from ulid import ULID
import sqlalchemy.types as types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ULIDType(TypeDecorator):
    """Custom ULID type for SQLAlchemy using ulid-py package."""
    
    impl = CHAR
    cache_ok = True
    
    def load_dialect_impl(self, dialect):
        return dialect.type_descriptor(CHAR(26))
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, ULID):
            return str(value)
        if isinstance(value, str):
            return value
        return str(ULID())
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return ULID.from_str(value)

class Users(Base):
    """Users model for authentication and profile management."""
    __tablename__ = "users"

    id = Column(ULIDType, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    salt = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Equipment(Base):
    """Equipment model for acrobatics classes/sessions."""
    __tablename__ = "equipment"

    id = Column(ULIDType, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String)
    media = Column(JSON)


class Location(Base):
    """Location model for acrobatics classes/sessions."""
    __tablename__ = "locations"

    id = Column(ULIDType, primary_key=True)
    name = Column(String(200), nullable=False)
    details = Column(JSON)
    equipment_ids = Column(JSON)


class Capabilities(Base):
    """Capabilities model for acrobatics classes/sessions."""
    __tablename__ = "capabilities"

    id = Column(ULIDType, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String)
    media = Column(JSON)


class Events(Base):
    """Events model for acrobatics classes/sessions."""
    __tablename__ = "events"

    id = Column(ULIDType, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String)
    prerequisite_ids = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EventSlot(Base):
    """Event slot model for acrobatics classes/sessions."""
    __tablename__ = "event_slots"

    id = Column(ULIDType, primary_key=True)
    location_id = Column(ULIDType, ForeignKey("locations.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    event_id = Column(ULIDType, ForeignKey("events.id"), nullable=False)
    day_number = Column(Integer, nullable=False)


class Attendees(Base):
    """Attendees model for acrobatics classes/sessions."""
    __tablename__ = "attendees"
    
    id = Column(ULIDType, primary_key=True)
    user_id = Column(ULIDType, ForeignKey("users.id"), nullable=False)
    event_id = Column(ULIDType, ForeignKey("events.id"), nullable=False)
    is_registered = Column(Boolean, default=False)


class Hosts(Base):
    """Hosts model for acrobatics classes/sessions."""
    __tablename__ = "hosts"
    
    id = Column(ULIDType, primary_key=True)
    attendee_id = Column(ULIDType, ForeignKey("attendees.id"), nullable=False)
    photos = Column(JSON)
    links = Column(JSON)
    

# Example of how to use the models in your FastAPI app:
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# This would typically be in your database.py file
DATABASE_URL = "mysql+pymysql://user:password@localhost/acro_planner"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

# Example usage in FastAPI endpoints:
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Example endpoint:
@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
"""