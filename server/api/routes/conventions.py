"""
Convention management routes for admin users.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import Conventions, Locations, EventSlot, Equipment, Attendees, Users
from api.auth import require_admin, require_attendee, get_current_user
from datetime import datetime, time
from api.schemas import (
    ConventionCreate, ConventionUpdate, ConventionResponse,
    LocationCreate, LocationUpdate, LocationResponse,
    EventSlotCreate, EventSlotUpdate, EventSlotResponse,
    ConventionRegistrationResponse, AttendeeConventionsResponse,
    BulkSlotCreationRequest, BulkSlotCreationResponse, TimeSlotCreate
)

router = APIRouter(prefix="/conventions", tags=["conventions"])


@router.post("/", response_model=ConventionResponse)
async def create_convention(
    convention: ConventionCreate,
    db: Session = Depends(get_db)
):
    """Create a new convention (admin only)."""
    new_convention = Conventions(
        id=str(uuid.uuid4()),
        name=convention.name,
        description=convention.description,
        start_date=convention.start_date.date(),
        end_date=convention.end_date.date(),
        is_active=True
    )
    db.add(new_convention)
    
    # Add locations if provided
    locations = []
    for loc_id in convention.location_ids:
        location = db.query(Locations).filter(Locations.id == loc_id).first()
        if location:
            location.convention_id = new_convention.id
            locations.append(location)
    
    db.commit()
    db.refresh(new_convention)
    
    return _format_convention_response(new_convention, locations, db)


@router.get("/", response_model=List[ConventionResponse])
async def list_conventions(db: Session = Depends(get_db)):
    """List all conventions (public)."""
    conventions = db.query(Conventions).filter(Conventions.is_active == True).all()
    return [_format_convention_response(c, _get_convention_locations(c.id, db), db) for c in conventions]


@router.get("/{convention_id}", response_model=ConventionResponse)
async def get_convention(convention_id: str, db: Session = Depends(get_db)):
    """Get convention details (public)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    locations = _get_convention_locations(convention_id, db)
    return _format_convention_response(convention, locations, db)


@router.put("/{convention_id}", response_model=ConventionResponse, dependencies=[Depends(require_admin)])
async def update_convention(
    convention_id: str,
    update: ConventionUpdate,
    db: Session = Depends(get_db)
):
    """Update convention details (admin only)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    if update.name is not None:
        convention.name = update.name
    if update.description is not None:
        convention.description = update.description
    if update.start_date is not None:
        convention.start_date = update.start_date.date()
    if update.end_date is not None:
        convention.end_date = update.end_date.date()
    
    if update.location_ids is not None:
        # Update location associations
        db.query(Locations).filter(Locations.convention_id == convention_id).update(
            {Locations.convention_id: None}
        )
        for loc_id in update.location_ids:
            location = db.query(Locations).filter(Locations.id == loc_id).first()
            if location:
                location.convention_id = convention_id
    
    db.commit()
    db.refresh(convention)
    
    locations = _get_convention_locations(convention_id, db)
    return _format_convention_response(convention, locations, db)


@router.delete("/{convention_id}", dependencies=[Depends(require_admin)])
async def delete_convention(convention_id: str, db: Session = Depends(get_db)):
    """Delete (deactivate) a convention (admin only)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    convention.is_active = False
    db.commit()
    
    return {"message": "Convention deleted successfully"}


# Location endpoints
@router.post("/{convention_id}/locations", response_model=LocationResponse, dependencies=[Depends(require_admin)])
async def add_location(
    convention_id: str,
    location: LocationCreate,
    db: Session = Depends(get_db)
):
    """Add a location to a convention (admin only)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    new_location = Locations(
        id=str(uuid.uuid4()),
        name=location.name,
        description=location.description,
        capacity=location.capacity,
        address=location.address,
        convention_id=convention_id
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return _format_location_response(new_location, db)


@router.put("/locations/{location_id}", response_model=LocationResponse, dependencies=[Depends(require_admin)])
async def update_location(
    location_id: str,
    update: LocationUpdate,
    db: Session = Depends(get_db)
):
    """Update location details (admin only)."""
    location = db.query(Locations).filter(Locations.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    if update.name is not None:
        location.name = update.name
    if update.description is not None:
        location.description = update.description
    if update.capacity is not None:
        location.capacity = update.capacity
    if update.address is not None:
        location.address = update.address
    
    db.commit()
    db.refresh(location)
    
    return _format_location_response(location, db)


@router.get("/locations/{location_id}", response_model=LocationResponse)
async def get_location(location_id: str, db: Session = Depends(get_db)):
    """Get location details (public)."""
    location = db.query(Locations).filter(Locations.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return _format_location_response(location, db)


# Event slot endpoints
@router.post("/{convention_id}/event-slots", response_model=EventSlotResponse, dependencies=[Depends(require_admin)])
async def create_event_slot(
    convention_id: str,
    slot: EventSlotCreate,
    db: Session = Depends(get_db)
):
    """Create an event slot for a convention (admin only)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    location = db.query(Locations).filter(Locations.id == slot.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Calculate day number
    day_number = (slot.start_time.date() - convention.start_date).days + 1
    
    new_slot = EventSlot(
        id=str(uuid.uuid4()),
        convention_id=convention_id,
        location_id=slot.location_id,
        start_time=slot.start_time,
        end_time=slot.end_time,
        day_number=day_number
    )
    db.add(new_slot)
    db.commit()
    db.refresh(new_slot)
    
    return _format_event_slot_response(new_slot, location)


@router.put("/event-slots/{slot_id}", response_model=EventSlotResponse, dependencies=[Depends(require_admin)])
async def update_event_slot(
    slot_id: str,
    update: EventSlotUpdate,
    db: Session = Depends(get_db)
):
    """Update an event slot (admin only)."""
    slot = db.query(EventSlot).filter(EventSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Event slot not found")
    
    if update.start_time is not None:
        slot.start_time = update.start_time
        # Recalculate day number
        convention = db.query(Conventions).filter(Conventions.id == slot.convention_id).first()
        slot.day_number = (update.start_time.date() - convention.start_date).days + 1
    if update.end_time is not None:
        slot.end_time = update.end_time
    if update.location_id is not None:
        location = db.query(Locations).filter(Locations.id == update.location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        slot.location_id = update.location_id
    
    db.commit()
    db.refresh(slot)
    
    location = db.query(Locations).filter(Locations.id == slot.location_id).first()
    return _format_event_slot_response(slot, location)


@router.get("/{convention_id}/event-slots", response_model=List[EventSlotResponse])
async def list_event_slots(convention_id: str, db: Session = Depends(get_db)):
    """List all event slots for a convention (public)."""
    slots = db.query(EventSlot).filter(EventSlot.convention_id == convention_id).all()
    result = []
    for slot in slots:
        location = db.query(Locations).filter(Locations.id == slot.location_id).first()
        result.append(_format_event_slot_response(slot, location))
    return result


@router.delete("/event-slots/{slot_id}", dependencies=[Depends(require_admin)])
async def delete_event_slot(slot_id: str, db: Session = Depends(get_db)):
    """Delete an event slot (admin only)."""
    slot = db.query(EventSlot).filter(EventSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Event slot not found")
    
    # Check if any events are scheduled in this slot
    if slot.event_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete slot with scheduled event. Remove event first."
        )
    
    db.delete(slot)
    db.commit()
    
    return {"message": "Event slot deleted successfully"}


# Helper functions
def _get_convention_locations(convention_id: str, db: Session) -> List[Locations]:
    """Get all locations for a convention."""
    return db.query(Locations).filter(Locations.convention_id == convention_id).all()


def _format_convention_response(convention: Conventions, locations: List[Locations], db: Session) -> dict:
    """Format convention response with related data."""
    event_slots = db.query(EventSlot).filter(EventSlot.convention_id == convention.id).all()
    
    return {
        "id": convention.id,
        "name": convention.name,
        "description": convention.description,
        "start_date": convention.start_date.isoformat() if convention.start_date else None,
        "end_date": convention.end_date.isoformat() if convention.end_date else None,
        "locations": [_format_location_response(loc, db) for loc in locations],
        "event_slots": [{"id": slot.id, "start_time": slot.start_time.isoformat(), 
                        "end_time": slot.end_time.isoformat()} for slot in event_slots],
        "created_at": convention.created_at.isoformat() if convention.created_at else None,
        "updated_at": convention.updated_at.isoformat() if convention.updated_at else None
    }


def _format_location_response(location: Locations, db: Session) -> dict:
    """Format location response with equipment."""
    equipment = db.query(Equipment).filter(Equipment.location_id == location.id).all()
    
    return {
        "id": location.id,
        "name": location.name,
        "description": location.description,
        "capacity": location.capacity,
        "address": location.address,
        "equipment": [{"id": e.id, "name": e.name, "quantity": e.quantity} for e in equipment],
        "created_at": location.created_at.isoformat() if location.created_at else None,
        "updated_at": location.updated_at.isoformat() if location.updated_at else None
    }


def _format_event_slot_response(slot: EventSlot, location: Locations) -> dict:
    """Format event slot response."""
    return {
        "id": slot.id,
        "convention_id": slot.convention_id,
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "location": _format_location_response(location, Session.object_session(slot)),
        "created_at": slot.created_at.isoformat() if slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot.updated_at else None
    }


# Convention Registration Endpoints
@router.post("/{convention_id}/register", response_model=ConventionRegistrationResponse, dependencies=[Depends(require_attendee)])
async def register_for_convention(
    convention_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Register attendee for a convention."""
    # Verify convention exists
    convention = db.query(Conventions).filter(
        Conventions.id == convention_id,
        Conventions.is_active == True
    ).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    # Get or create attendee record
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user["id"]).first()
    if not attendee:
        attendee = Attendees(
            id=str(uuid.uuid4()),
            user_id=current_user["id"],
            convention_id=convention_id,
            is_registered=True
        )
        db.add(attendee)
    else:
        # Check if already registered for this convention
        if attendee.convention_id == convention_id and attendee.is_registered:
            raise HTTPException(status_code=400, detail="Already registered for this convention")
        
        # Update attendee record
        attendee.convention_id = convention_id
        attendee.is_registered = True
    
    db.commit()
    db.refresh(attendee)
    
    return {
        "registration_id": attendee.id,
        "convention_id": convention_id,
        "convention_name": convention.name,
        "attendee_id": attendee.id,
        "attendee_name": current_user["name"],
        "is_registered": True,
        "created_at": attendee.created_at.isoformat() if attendee.created_at else datetime.now().isoformat()
    }


@router.get("/{convention_id}/attendees", response_model=List[ConventionRegistrationResponse], dependencies=[Depends(require_admin)])
async def list_convention_attendees(
    convention_id: str,
    db: Session = Depends(get_db)
):
    """List all attendees registered for a convention (admin only)."""
    # Verify convention exists
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    # Get all registered attendees
    attendees = db.query(Attendees).filter(
        Attendees.convention_id == convention_id,
        Attendees.is_registered == True
    ).all()
    
    result = []
    for attendee in attendees:
        user = db.query(Users).filter(Users.id == attendee.user_id).first()
        result.append({
            "registration_id": attendee.id,
            "convention_id": convention_id,
            "convention_name": convention.name,
            "attendee_id": attendee.id,
            "attendee_name": user.name if user else "Unknown",
            "is_registered": attendee.is_registered,
            "created_at": attendee.created_at.isoformat() if attendee.created_at else datetime.now().isoformat()
        })
    
    return result


# Bulk Slot Creation Endpoint
@router.post("/{convention_id}/bulk-slots", response_model=BulkSlotCreationResponse, dependencies=[Depends(require_admin)])
async def create_bulk_slots(
    convention_id: str,
    request: BulkSlotCreationRequest,
    db: Session = Depends(get_db)
):
    """Create multiple event slots for a convention (admin only)."""
    # Verify convention exists
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    # Verify all locations exist and belong to this convention
    locations = []
    for loc_id in request.location_ids:
        location = db.query(Locations).filter(
            Locations.id == loc_id,
            Locations.convention_id == convention_id
        ).first()
        if not location:
            raise HTTPException(status_code=404, detail=f"Location {loc_id} not found in this convention")
        locations.append(location)
    
    # Parse time slots and create datetime objects
    time_slots = []
    base_date = convention.start_date
    for ts in request.time_slots:
        start_parts = ts.start_time.split(":")
        end_parts = ts.end_time.split(":")
        
        start_time = time(int(start_parts[0]), int(start_parts[1]))
        end_time = time(int(end_parts[0]), int(end_parts[1]))
        
        if end_time <= start_time:
            raise HTTPException(
                status_code=400, 
                detail=f"End time {ts.end_time} must be after start time {ts.start_time}"
            )
        
        time_slots.append((start_time, end_time))
    
    # Create slots
    created_slots = []
    for day_number in range(1, request.number_of_days + 1):
        current_date = base_date + timedelta(days=day_number - 1)
        
        for start_time, end_time in time_slots:
            for location in locations:
                start_datetime = datetime.combine(current_date, start_time)
                end_datetime = datetime.combine(current_date, end_time)
                
                slot = EventSlot(
                    id=str(uuid.uuid4()),
                    convention_id=convention_id,
                    location_id=location.id,
                    start_time=start_datetime,
                    end_time=end_datetime,
                    day_number=day_number,
                    event_id=None
                )
                db.add(slot)
                created_slots.append(slot)
    
    db.commit()
    
    # Format response
    formatted_slots = []
    for slot in created_slots:
        db.refresh(slot)
        location = next(loc for loc in locations if loc.id == slot.location_id)
        formatted_slots.append(_format_event_slot_response(slot, location))
    
    return {
        "convention_id": convention_id,
        "total_slots_created": len(created_slots),
        "slots": formatted_slots
    }


@router.get("/{convention_id}/schedule", response_model=dict)
async def get_convention_schedule(convention_id: str, db: Session = Depends(get_db)):
    """Get full convention schedule with all workshops and slots (public)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    # Get all event slots for this convention
    from models import Events
    slots = db.query(EventSlot).filter(EventSlot.convention_id == convention_id).all()
    
    # Organize schedule by day and time
    schedule = {}
    for slot in slots:
        day = getattr(slot, 'day_number', 1)
        if day not in schedule:
            schedule[day] = []
        
        # Get location
        location = db.query(Locations).filter(Locations.id == slot.location_id).first()
        
        # Get workshop if assigned
        workshop = None
        if slot.event_id:
            event = db.query(Events).filter(Events.id == slot.event_id).first()
            if event:
                # Simplified workshop response for schedule
                from models import HostEvents, Hosts
                host_event = db.query(HostEvents).filter(HostEvents.event_id == event.id).first()
                host = None
                if host_event:
                    host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
                    user = db.query(Users).filter(Users.id == host.user_id).first() if host else None
                
                workshop = {
                    "id": event.id,
                    "name": event.name,
                    "description": event.description,
                    "host_name": user.name if 'user' in locals() and user else None,
                    "max_students": event.max_students
                }
        
        schedule[day].append({
            "slot": _format_event_slot_response(slot, location),
            "workshop": workshop
        })
    
    # Sort each day by start time
    for day in schedule:
        schedule[day].sort(key=lambda x: x["slot"]["start_time"])
    
    return {
        "convention_id": convention_id,
        "convention_name": convention.name,
        "schedule": schedule
    }


@router.get("/{convention_id}/attendees", response_model=List[dict], dependencies=[Depends(require_admin)])
async def get_convention_attendees(convention_id: str, db: Session = Depends(get_db)):
    """Get all attendees registered for a convention (admin only)."""
    convention = db.query(Conventions).filter(Conventions.id == convention_id).first()
    if not convention:
        raise HTTPException(status_code=404, detail="Convention not found")
    
    # Get all attendees for this convention
    attendees = db.query(Attendees).filter(Attendees.convention_id == convention_id).all()
    
    result = []
    for attendee in attendees:
        user = db.query(Users).filter(Users.id == attendee.user_id).first()
        
        # Get their workshop selections
        from models import Selections
        selections = db.query(Selections).filter(Selections.attendee_id == attendee.id).all()
        selection_count = {
            "committed": sum(1 for s in selections if s.commitment_level == "committed"),
            "interested": sum(1 for s in selections if s.commitment_level == "interested"),
            "maybe": sum(1 for s in selections if s.commitment_level == "maybe")
        }
        
        result.append({
            "attendee_id": attendee.id,
            "attendee_name": user.name if user else None,
            "email": user.email if user else None,
            "selections": selection_count,
            "total_selections": len(selections)
        })
    
    return result