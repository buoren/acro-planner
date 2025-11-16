"""
Attendee selection and schedule management routes.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ulid import ULID

from database import get_db
from models import Attendees, Selections, Events, EventSlot, Users, Locations, Capabilities
from api.auth import require_auth, get_current_user, require_attendee
from api.schemas import (
    WorkshopSelectionCreate, WorkshopSelectionUpdate, WorkshopSelectionResponse,
    AttendeeScheduleResponse, WorkshopResponse
)

router = APIRouter(prefix="/attendees", tags=["attendees"])


@router.post("/selections", response_model=WorkshopSelectionResponse, dependencies=[Depends(require_attendee)])
async def select_workshop(
    selection: WorkshopSelectionCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Select a workshop as a possibility (attendee only)."""
    # Get attendee record
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee record not found")
    
    # Use the attendee ID from current user if not provided
    if not selection.attendee_id or selection.attendee_id != attendee.id:
        selection.attendee_id = attendee.id
    
    # Verify workshop exists
    workshop = db.query(Events).filter(Events.id == selection.workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Verify event slot exists
    event_slot = db.query(EventSlot).filter(EventSlot.id == selection.event_slot_id).first()
    if not event_slot:
        raise HTTPException(status_code=404, detail="Event slot not found")
    
    # Check if workshop is scheduled for this slot
    if event_slot.event_id and event_slot.event_id != workshop.id:
        raise HTTPException(
            status_code=400,
            detail="Workshop is not scheduled for this event slot"
        )
    
    # Check if already selected
    existing = db.query(Selections).filter(
        Selections.attendee_id == attendee.id,
        Selections.event_id == selection.workshop_id,
        Selections.event_slot_id == selection.event_slot_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Workshop already selected for this slot")
    
    # Check for time conflicts if committing
    if selection.commitment_level == "committed":
        # Check for other committed workshops at the same time
        conflicts = db.query(Selections).filter(
            Selections.attendee_id == attendee.id,
            Selections.event_slot_id == selection.event_slot_id,
            Selections.commitment_level == "committed"
        ).first()
        
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail="Already committed to another workshop at this time"
            )
        
        # Check if workshop is full
        committed_count = db.query(Selections).filter(
            Selections.event_id == selection.workshop_id,
            Selections.commitment_level == "committed"
        ).count()
        
        if committed_count >= workshop.max_students:
            raise HTTPException(status_code=400, detail="Workshop is full")
    
    # Create selection
    new_selection = Selections(
        id=str(ULID()),
        attendee_id=attendee.id,
        event_id=selection.workshop_id,
        event_slot_id=selection.event_slot_id,
        commitment_level=selection.commitment_level,
        is_selected=True
    )
    db.add(new_selection)
    db.commit()
    db.refresh(new_selection)
    
    return _format_selection_response(new_selection, db)


@router.put("/selections/{selection_id}", response_model=WorkshopSelectionResponse, dependencies=[Depends(require_attendee)])
async def update_workshop_selection(
    selection_id: str,
    update: WorkshopSelectionUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update workshop selection commitment level (attendee only)."""
    selection = db.query(Selections).filter(Selections.id == selection_id).first()
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    # Verify ownership
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee or selection.attendee_id != attendee.id:
        raise HTTPException(status_code=403, detail="Can only update your own selections")
    
    # If upgrading to committed, check for conflicts and capacity
    if update.commitment_level == "committed" and selection.commitment_level != "committed":
        # Check for time conflicts
        conflicts = db.query(Selections).filter(
            Selections.attendee_id == attendee.id,
            Selections.event_slot_id == selection.event_slot_id,
            Selections.commitment_level == "committed",
            Selections.id != selection_id
        ).first()
        
        if conflicts:
            raise HTTPException(
                status_code=400,
                detail="Already committed to another workshop at this time"
            )
        
        # Check workshop capacity
        workshop = db.query(Events).filter(Events.id == selection.event_id).first()
        committed_count = db.query(Selections).filter(
            Selections.event_id == selection.event_id,
            Selections.commitment_level == "committed"
        ).count()
        
        if committed_count >= workshop.max_students:
            raise HTTPException(status_code=400, detail="Workshop is full")
    
    selection.commitment_level = update.commitment_level
    db.commit()
    db.refresh(selection)
    
    return _format_selection_response(selection, db)


@router.delete("/selections/{selection_id}", dependencies=[Depends(require_attendee)])
async def remove_workshop_selection(
    selection_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Remove a workshop selection (attendee only)."""
    selection = db.query(Selections).filter(Selections.id == selection_id).first()
    if not selection:
        raise HTTPException(status_code=404, detail="Selection not found")
    
    # Verify ownership
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee or selection.attendee_id != attendee.id:
        raise HTTPException(status_code=403, detail="Can only remove your own selections")
    
    db.delete(selection)
    db.commit()
    
    return {"message": "Selection removed successfully"}


@router.post("/commit/{workshop_id}", response_model=WorkshopSelectionResponse, dependencies=[Depends(require_attendee)])
async def commit_to_workshop(
    workshop_id: str,
    event_slot_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Commit to a workshop (attendee only)."""
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee record not found")
    
    # Check if already selected
    selection = db.query(Selections).filter(
        Selections.attendee_id == attendee.id,
        Selections.event_id == workshop_id,
        Selections.event_slot_id == event_slot_id
    ).first()
    
    if selection:
        # Update existing selection to committed
        if selection.commitment_level == "committed":
            raise HTTPException(status_code=400, detail="Already committed to this workshop")
        
        selection.commitment_level = "committed"
        db.commit()
        db.refresh(selection)
        return _format_selection_response(selection, db)
    else:
        # Create new selection as committed
        selection_data = WorkshopSelectionCreate(
            attendee_id=attendee.id,
            workshop_id=workshop_id,
            event_slot_id=event_slot_id,
            commitment_level="committed"
        )
        return await select_workshop(selection_data, db, current_user)


@router.get("/schedule", response_model=AttendeeScheduleResponse, dependencies=[Depends(require_attendee)])
async def get_my_schedule(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get my workshop schedule (attendee only)."""
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee record not found")
    
    return _format_schedule_response(attendee, db)


@router.get("/{attendee_id}/schedule", response_model=AttendeeScheduleResponse)
async def get_attendee_schedule(attendee_id: str, db: Session = Depends(get_db)):
    """Get an attendee's workshop schedule (public)."""
    attendee = db.query(Attendees).filter(Attendees.id == attendee_id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    
    return _format_schedule_response(attendee, db)


@router.get("/workshops/filtered", response_model=List[WorkshopResponse])
async def filter_workshops_by_prerequisites(
    max_fulfilled: bool = Query(True, description="Only show workshops where I can fulfill prerequisites"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Filter workshops by prerequisites I can fulfill (authenticated)."""
    # Get attendee's capabilities (for this example, we'll assume they track completed workshops)
    attendee = db.query(Attendees).filter(Attendees.user_id == current_user.id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee record not found")
    
    # Get all completed workshop IDs (committed and attended)
    completed_workshops = db.query(Selections.event_id).filter(
        Selections.attendee_id == attendee.id,
        Selections.commitment_level == "committed"
    ).all()
    completed_ids = [w[0] for w in completed_workshops]
    
    # Build set of fulfilled capabilities from completed workshops
    fulfilled_capabilities = set()
    for workshop_id in completed_ids:
        workshop = db.query(Events).filter(Events.id == workshop_id).first()
        if workshop:
            # Add this workshop as a capability
            capability = db.query(Capabilities).filter(Capabilities.name == workshop.name).first()
            if capability:
                fulfilled_capabilities.add(capability.id)
    
    # Get all workshops
    workshops = db.query(Events).all()
    result = []
    
    for workshop in workshops:
        if max_fulfilled and workshop.prerequisite_ids:
            # Check if attendee can fulfill all prerequisites
            workshop_prereqs = set(workshop.prerequisite_ids)
            if not workshop_prereqs.issubset(fulfilled_capabilities):
                continue
        
        result.append(_format_workshop_response_simple(workshop, db))
    
    return result


# Helper functions
def _format_selection_response(selection: Selections, db: Session) -> dict:
    """Format workshop selection response."""
    attendee = db.query(Attendees).filter(Attendees.id == selection.attendee_id).first()
    user = db.query(Users).filter(Users.id == attendee.user_id).first() if attendee else None
    workshop = db.query(Events).filter(Events.id == selection.event_id).first()
    event_slot = db.query(EventSlot).filter(EventSlot.id == selection.event_slot_id).first()
    
    workshop_resp = _format_workshop_response_simple(workshop, db) if workshop else {}
    slot_resp = _format_event_slot_response_simple(event_slot, db) if event_slot else {}
    
    return {
        "id": selection.id,
        "attendee_id": selection.attendee_id,
        "attendee_name": user.name if user else None,
        "workshop": workshop_resp,
        "event_slot": slot_resp,
        "commitment_level": selection.commitment_level,
        "created_at": selection.created_at.isoformat() if selection.created_at else None,
        "updated_at": selection.updated_at.isoformat() if selection.updated_at else None
    }


def _format_schedule_response(attendee: Attendees, db: Session) -> dict:
    """Format attendee schedule response."""
    user = db.query(Users).filter(Users.id == attendee.user_id).first()
    
    # Get all selections
    selections = db.query(Selections).filter(Selections.attendee_id == attendee.id).all()
    
    # Count by commitment level
    committed = 0
    interested = 0
    maybe = 0
    
    formatted_selections = []
    for selection in selections:
        formatted_selections.append(_format_selection_response(selection, db))
        
        if selection.commitment_level == "committed":
            committed += 1
        elif selection.commitment_level == "interested":
            interested += 1
        elif selection.commitment_level == "maybe":
            maybe += 1
    
    return {
        "attendee_id": attendee.id,
        "attendee_name": user.name if user else None,
        "selections": formatted_selections,
        "committed_count": committed,
        "interested_count": interested,
        "maybe_count": maybe
    }


def _format_workshop_response_simple(workshop: Events, db: Session) -> dict:
    """Simple workshop format for attendee endpoints."""
    from models import HostEvents, Hosts
    
    # Get host info
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop.id).first()
    host_name = None
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host:
            user = db.query(Users).filter(Users.id == host.user_id).first()
            host_name = user.name if user else None
    
    # Count current students
    current_students = db.query(Selections).filter(
        Selections.event_id == workshop.id,
        Selections.commitment_level == "committed"
    ).count()
    
    return {
        "id": workshop.id,
        "name": workshop.name,
        "description": workshop.description,
        "host_id": host_event.host_id if host_event else None,
        "host_name": host_name,
        "max_students": workshop.max_students,
        "current_students": current_students,
        "prerequisites": [],  # Simplified
        "equipment": [],  # Simplified
        "event_slots": [],  # Simplified
        "created_at": workshop.created_at.isoformat() if workshop.created_at else None,
        "updated_at": workshop.updated_at.isoformat() if workshop.updated_at else None
    }


def _format_event_slot_response_simple(slot: EventSlot, db: Session) -> dict:
    """Simple event slot format for attendee endpoints."""
    location = db.query(Locations).filter(Locations.id == slot.location_id).first() if slot else None
    
    return {
        "id": slot.id if slot else None,
        "convention_id": slot.convention_id if slot else None,
        "start_time": slot.start_time.isoformat() if slot and slot.start_time else None,
        "end_time": slot.end_time.isoformat() if slot and slot.end_time else None,
        "location": {
            "id": location.id if location else None,
            "name": location.name if location else None,
            "description": location.description if location else None,
            "capacity": location.capacity if location else None,
            "address": location.address if location else None,
            "equipment": [],
            "created_at": location.created_at.isoformat() if location and location.created_at else None,
            "updated_at": location.updated_at.isoformat() if location and location.updated_at else None
        } if location else {},
        "created_at": slot.created_at.isoformat() if slot and slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot and slot.updated_at else None
    }


@router.get("/{attendee_id}/capabilities", response_model=List[dict])
async def get_attendee_capabilities(attendee_id: str, db: Session = Depends(get_db)):
    """Get attendee's fulfilled capabilities (public)."""
    attendee = db.query(Attendees).filter(Attendees.id == attendee_id).first()
    if not attendee:
        raise HTTPException(status_code=404, detail="Attendee not found")
    
    capabilities = []
    if attendee.capability_ids:
        for cap_id in attendee.capability_ids:
            capability = db.query(Capabilities).filter(Capabilities.id == cap_id).first()
            if capability:
                capabilities.append({
                    "id": capability.id,
                    "name": capability.name,
                    "description": capability.description,
                    "created_at": capability.created_at.isoformat() if capability.created_at else None,
                    "updated_at": capability.updated_at.isoformat() if capability.updated_at else None
                })
    
    return capabilities