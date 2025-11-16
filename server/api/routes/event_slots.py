"""
Event slot management routes and slot-workshop assignment queries.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import EventSlot, Events, Locations, HostEvents, Users, Hosts
from api.auth import require_auth
from api.schemas import SlotWorkshopResponse, EventSlotResponse

router = APIRouter(prefix="/event-slots", tags=["event-slots"])


@router.get("/{slot_id}/workshop", response_model=SlotWorkshopResponse)
async def get_slot_workshop(slot_id: str, db: Session = Depends(get_db)):
    """Get workshop assigned to an event slot (public)."""
    slot = db.query(EventSlot).filter(EventSlot.id == slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Event slot not found")
    
    location = db.query(Locations).filter(Locations.id == slot.location_id).first()
    
    workshop = None
    if slot.event_id:
        event = db.query(Events).filter(Events.id == slot.event_id).first()
        if event:
            workshop = _format_workshop_simple(event, db)
    
    return {
        "event_slot": _format_event_slot_response(slot, location),
        "workshop": workshop
    }


@router.get("/", response_model=List[EventSlotResponse])
async def list_event_slots(
    convention_id: Optional[str] = Query(None),
    available_only: bool = Query(False),
    location_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """List event slots with optional filters (public)."""
    query = db.query(EventSlot)
    
    if convention_id:
        query = query.filter(EventSlot.convention_id == convention_id)
    
    if available_only:
        query = query.filter(EventSlot.event_id.is_(None))
    
    if location_id:
        query = query.filter(EventSlot.location_id == location_id)
    
    slots = query.all()
    result = []
    
    for slot in slots:
        location = db.query(Locations).filter(Locations.id == slot.location_id).first()
        result.append(_format_event_slot_response(slot, location))
    
    return result


# Helper functions
def _format_event_slot_response(slot: EventSlot, location: Optional[Locations]) -> dict:
    """Format event slot response with location details."""
    location_data = None
    if location:
        location_data = {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "capacity": location.capacity,
            "address": location.address,
            "equipment": [],  # Simplified
            "created_at": location.created_at.isoformat() if location.created_at else None,
            "updated_at": location.updated_at.isoformat() if location.updated_at else None
        }
    
    return {
        "id": slot.id,
        "convention_id": slot.convention_id,
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "location": location_data,
        "created_at": slot.created_at.isoformat() if slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot.updated_at else None
    }


def _format_workshop_simple(workshop: Events, db: Session) -> dict:
    """Format simplified workshop response."""
    # Get host information
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop.id).first()
    host = None
    host_user = None
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host:
            host_user = db.query(Users).filter(Users.id == host.user_id).first()
    
    return {
        "id": workshop.id,
        "name": workshop.name,
        "description": workshop.description,
        "host_id": host.id if host else None,
        "host_name": host_user.name if host_user else None,
        "max_students": workshop.max_students,
        "current_students": 0,  # Simplified - would calculate if needed
        "prerequisites": [],  # Simplified
        "equipment": [],  # Simplified
        "event_slots": [],  # Simplified
        "created_at": workshop.created_at.isoformat() if workshop.created_at else None,
        "updated_at": workshop.updated_at.isoformat() if workshop.updated_at else None
    }