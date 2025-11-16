"""
SQLAlchemy models for Acro Planner application.

This file contains example models to demonstrate the structure.
Replace with your actual models as needed.
"""


from sqlalchemy import JSON, Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
# Import Base from database.py to share the same metadata
from database import Base


class Users(Base):
    """Users model for authentication and profile management."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    salt = Column(String(255), nullable=True)  # Nullable for OAuth-only users
    oauth_only = Column(Boolean, default=False, nullable=False)  # Flag for OAuth-only users
    user_info = Column(JSON, nullable=True)
    contact_info = Column(JSON, nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class PasswordResetToken(Base):
    """Password reset token model for forgot password functionality."""
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    user = relationship("Users", backref="password_reset_tokens")


class SystemSetting(Base):
    """System settings model for storing configuration key-value pairs."""
    __tablename__ = "system_settings"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Equipment(Base):
    """Equipment model for acrobatics classes/sessions."""
    __tablename__ = "equipment"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    media = Column(JSON)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=True)
    quantity = Column(Integer, default=1)
    convention_id = Column(String(36), ForeignKey("conventions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Locations(Base):
    """Location model for acrobatics classes/sessions."""
    __tablename__ = "locations"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    capacity = Column(Integer)
    address = Column(String(500))
    details = Column(JSON)
    equipment_ids = Column(JSON)
    convention_id = Column(String(36), ForeignKey("conventions.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Capabilities(Base):
    """Capabilities model for acrobatics classes/sessions."""
    __tablename__ = "capabilities"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    parent_capability_ids = Column(JSON)  # For prerequisite chaining
    media = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Events(Base):
    """Events model for acrobatics classes/sessions (workshops)."""
    __tablename__ = "events"

    id = Column(String(36), primary_key=True)
    convention_id = Column(String(36), ForeignKey("conventions.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    prerequisite_ids = Column(JSON)
    equipment_ids = Column(JSON)
    max_students = Column(Integer, default=20)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EventSlot(Base):
    """Event slot model for acrobatics classes/sessions."""
    __tablename__ = "event_slots"

    id = Column(String(36), primary_key=True)
    convention_id = Column(String(36), ForeignKey("conventions.id"), nullable=False)
    location_id = Column(String(36), ForeignKey("locations.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=True)
    day_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Conventions(Base):
    """Conventions model for acrobatics conventions/gatherings."""
    __tablename__ = "conventions"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    location = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Attendees(Base):
    """Attendees model for users attending acrobatics conventions."""
    __tablename__ = "attendees"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    convention_id = Column(String(36), ForeignKey("conventions.id"), nullable=True)  # Nullable for general attendee role
    is_registered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Hosts(Base):
    """Hosts model for acrobatics classes/sessions."""
    __tablename__ = "hosts"

    id = Column(String(36), primary_key=True)
    attendee_id = Column(String(36), ForeignKey("attendees.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    available_slot_ids = Column(JSON)  # Available event slots
    photos = Column(JSON)
    links = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class HostEvents(Base):
    """Host events join table for acrobatics classes/sessions."""
    __tablename__ = "host_events"

    id = Column(String(36), primary_key=True)
    host_id = Column(String(36), ForeignKey("hosts.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Admins(Base):
    """Admins model for administrative users."""
    __tablename__ = "admins"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Selections(Base):
    """Selections model for user's choices of events."""
    __tablename__ = "selections"

    id = Column(String(36), primary_key=True)
    attendee_id = Column(String(36), ForeignKey("attendees.id"), nullable=False)
    event_id = Column(String(36), ForeignKey("events.id"), nullable=False)
    event_slot_id = Column(String(36), ForeignKey("event_slots.id"), nullable=True)
    commitment_level = Column(String(20), default="interested")  # interested, maybe, committed
    is_selected = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


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
