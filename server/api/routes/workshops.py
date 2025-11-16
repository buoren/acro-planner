"""
Workshop (Event) management routes for hosts.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ulid import ULID

from database import get_db
from models import Events, Hosts, HostEvents, EventSlot, Capabilities, Equipment, Users, Selections, Locations
from api.auth import require_host_or_admin, require_auth, get_current_user
from api.schemas import (
    WorkshopCreate, WorkshopUpdate, WorkshopResponse, 
    WorkshopFilterParams, WorkshopShareResponse,
    HostAvailabilityCreate, HostAvailabilityResponse,
    WorkshopSlotAssignmentCreate, WorkshopSlotAssignmentResponse, SlotWorkshopResponse
)

router = APIRouter(prefix="/workshops", tags=["workshops"])


@router.post("/", response_model=WorkshopResponse, dependencies=[Depends(require_host_or_admin)])
async def create_workshop(
    workshop: WorkshopCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Create a new workshop (host or admin)."""
    # Verify host exists
    host = db.query(Hosts).filter(Hosts.id == workshop.host_id).first()
    if not host:
        # If current user is a host, use their host ID
        host = db.query(Hosts).filter(Hosts.user_id == current_user.id).first()
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        workshop.host_id = host.id
    
    # Verify prerequisites exist
    for prereq_id in workshop.prerequisite_ids:
        prerequisite = db.query(Capabilities).filter(Capabilities.id == prereq_id).first()
        if not prerequisite:
            raise HTTPException(status_code=404, detail=f"Prerequisite {prereq_id} not found")
    
    # Verify equipment exists
    for equip_id in workshop.equipment_ids:
        equipment = db.query(Equipment).filter(Equipment.id == equip_id).first()
        if not equipment:
            raise HTTPException(status_code=404, detail=f"Equipment {equip_id} not found")
    
    # Get convention ID from host's attendee record
    from models import Attendees
    attendee = db.query(Attendees).filter(Attendees.id == host.attendee_id).first()
    convention_id = attendee.convention_id if attendee else None
    
    new_workshop = Events(
        id=str(ULID()),
        name=workshop.name,
        description=workshop.description,
        max_students=workshop.max_students,
        prerequisite_ids=workshop.prerequisite_ids,
        equipment_ids=workshop.equipment_ids,
        convention_id=convention_id
    )
    db.add(new_workshop)
    
    # Create host-event relationship
    host_event = HostEvents(
        id=str(ULID()),
        host_id=workshop.host_id,
        event_id=new_workshop.id
    )
    db.add(host_event)
    
    db.commit()
    db.refresh(new_workshop)
    
    return _format_workshop_response(new_workshop, db)


@router.get("/", response_model=List[WorkshopResponse])
async def list_workshops(
    convention_id: Optional[str] = Query(None),
    host_id: Optional[str] = Query(None),
    has_space: bool = Query(True),
    db: Session = Depends(get_db)
):
    """List all workshops (public), with optional filters."""
    query = db.query(Events)
    
    if convention_id:
        query = query.filter(Events.convention_id == convention_id)
    
    workshops = query.all()
    result = []
    
    for workshop in workshops:
        # Filter by host if specified
        if host_id:
            host_event = db.query(HostEvents).filter(
                HostEvents.event_id == workshop.id,
                HostEvents.host_id == host_id
            ).first()
            if not host_event:
                continue
        
        # Filter by space availability if specified
        if has_space:
            student_count = db.query(Selections).filter(
                Selections.event_id == workshop.id,
                Selections.commitment_level == "committed"
            ).count()
            if student_count >= workshop.max_students:
                continue
        
        result.append(_format_workshop_response(workshop, db))
    
    return result


@router.get("/{workshop_id}", response_model=WorkshopResponse)
async def get_workshop(workshop_id: str, db: Session = Depends(get_db)):
    """Get workshop details (public)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    return _format_workshop_response(workshop, db)


@router.put("/{workshop_id}", response_model=WorkshopResponse, dependencies=[Depends(require_host_or_admin)])
async def update_workshop(
    workshop_id: str,
    update: WorkshopUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Update workshop details (host who owns it or admin)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Check if current user is the host of this workshop (unless admin)
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop_id).first()
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host and host.user_id != current_user.id:
            # Check if user is admin
            from models import Admins
            is_admin = db.query(Admins).filter(Admins.user_id == current_user.id).first()
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only the workshop host or admin can update this workshop")
    
    if update.name is not None:
        workshop.name = update.name
    if update.description is not None:
        workshop.description = update.description
    if update.max_students is not None:
        workshop.max_students = update.max_students
    if update.prerequisite_ids is not None:
        # Verify prerequisites exist
        for prereq_id in update.prerequisite_ids:
            prerequisite = db.query(Capabilities).filter(Capabilities.id == prereq_id).first()
            if not prerequisite:
                raise HTTPException(status_code=404, detail=f"Prerequisite {prereq_id} not found")
        workshop.prerequisite_ids = update.prerequisite_ids
    if update.equipment_ids is not None:
        # Verify equipment exists
        for equip_id in update.equipment_ids:
            equipment = db.query(Equipment).filter(Equipment.id == equip_id).first()
            if not equipment:
                raise HTTPException(status_code=404, detail=f"Equipment {equip_id} not found")
        workshop.equipment_ids = update.equipment_ids
    
    db.commit()
    db.refresh(workshop)
    
    return _format_workshop_response(workshop, db)


@router.delete("/{workshop_id}", dependencies=[Depends(require_host_or_admin)])
async def delete_workshop(
    workshop_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Delete a workshop (host who owns it or admin)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Check if current user is the host of this workshop (unless admin)
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop_id).first()
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host and host.user_id != current_user.id:
            # Check if user is admin
            from models import Admins
            is_admin = db.query(Admins).filter(Admins.user_id == current_user.id).first()
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only the workshop host or admin can delete this workshop")
    
    # Delete host-event relationships
    db.query(HostEvents).filter(HostEvents.event_id == workshop_id).delete()
    
    # Delete any selections for this workshop
    db.query(Selections).filter(Selections.event_id == workshop_id).delete()
    
    # Clear event_id from any event slots
    db.query(EventSlot).filter(EventSlot.event_id == workshop_id).update({EventSlot.event_id: None})
    
    db.delete(workshop)
    db.commit()
    
    return {"message": "Workshop deleted successfully"}


@router.post("/{workshop_id}/add-prerequisite", response_model=WorkshopResponse, dependencies=[Depends(require_host_or_admin)])
async def add_workshop_prerequisite(
    workshop_id: str,
    prerequisite_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add a prerequisite to a workshop (host or admin)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    prerequisite = db.query(Capabilities).filter(Capabilities.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    
    # Add prerequisite if not already present
    prereq_ids = workshop.prerequisite_ids or []
    if prerequisite_id not in prereq_ids:
        prereq_ids.append(prerequisite_id)
        workshop.prerequisite_ids = prereq_ids
        db.commit()
        db.refresh(workshop)
    
    return _format_workshop_response(workshop, db)


@router.post("/{workshop_id}/add-equipment", response_model=WorkshopResponse, dependencies=[Depends(require_host_or_admin)])
async def add_workshop_equipment(
    workshop_id: str,
    equipment_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Add equipment requirement to a workshop (host or admin)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    # Add equipment if not already present
    equip_ids = workshop.equipment_ids or []
    if equipment_id not in equip_ids:
        equip_ids.append(equipment_id)
        workshop.equipment_ids = equip_ids
        db.commit()
        db.refresh(workshop)
    
    return _format_workshop_response(workshop, db)


@router.post("/host-availability", response_model=HostAvailabilityResponse, dependencies=[Depends(require_host_or_admin)])
async def set_host_availability(
    availability: HostAvailabilityCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Set host availability for event slots (host or admin)."""
    # Verify host exists
    host = db.query(Hosts).filter(Hosts.id == availability.host_id).first()
    if not host:
        # If no host_id provided, use current user's host record
        host = db.query(Hosts).filter(Hosts.user_id == current_user.id).first()
        if not host:
            raise HTTPException(status_code=404, detail="Host not found")
        availability.host_id = host.id
    
    # Verify all event slots exist
    for slot_id in availability.event_slot_ids:
        slot = db.query(EventSlot).filter(EventSlot.id == slot_id).first()
        if not slot:
            raise HTTPException(status_code=404, detail=f"Event slot {slot_id} not found")
    
    # Update host's available slots
    host.available_slot_ids = availability.event_slot_ids
    db.commit()
    db.refresh(host)
    
    return _format_host_availability_response(host, db)


@router.get("/hosts/{host_id}/availability", response_model=HostAvailabilityResponse)
async def get_host_availability(host_id: str, db: Session = Depends(get_db)):
    """Get host availability (public)."""
    host = db.query(Hosts).filter(Hosts.id == host_id).first()
    if not host:
        raise HTTPException(status_code=404, detail="Host not found")
    
    return _format_host_availability_response(host, db)


@router.get("/{workshop_id}/share", response_model=WorkshopShareResponse)
async def get_workshop_share_link(workshop_id: str, db: Session = Depends(get_db)):
    """Get shareable link for a workshop (public)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Generate share URL (in production, this would use the actual domain)
    share_url = f"https://acro-planner.com/workshops/{workshop_id}"
    
    return {
        "workshop_id": workshop_id,
        "workshop_name": workshop.name,
        "share_url": share_url,
        "description": workshop.description
    }


@router.post("/browse", response_model=List[WorkshopResponse])
async def browse_workshops(
    filters: WorkshopFilterParams,
    db: Session = Depends(get_db),
    current_user = Depends(require_auth)
):
    """Browse workshops with filters (authenticated users)."""
    query = db.query(Events)
    
    if filters.convention_id:
        query = query.filter(Events.convention_id == filters.convention_id)
    
    if filters.event_slot_id:
        query = query.filter(EventSlot.id == filters.event_slot_id, EventSlot.event_id == Events.id)
    
    workshops = query.all()
    result = []
    
    for workshop in workshops:
        # Filter by prerequisite fulfillment if specified
        if filters.can_fulfill_prerequisites and filters.attendee_capabilities:
            workshop_prereqs = set(workshop.prerequisite_ids or [])
            if workshop_prereqs and not workshop_prereqs.issubset(set(filters.attendee_capabilities)):
                continue
        
        # Filter by space availability if specified
        if filters.has_space:
            student_count = db.query(Selections).filter(
                Selections.event_id == workshop.id,
                Selections.commitment_level == "committed"
            ).count()
            if student_count >= workshop.max_students:
                continue
        
        result.append(_format_workshop_response(workshop, db))
    
    return result


# Event-to-Slot Assignment Endpoints

@router.post("/{workshop_id}/assign-slot", response_model=WorkshopSlotAssignmentResponse, dependencies=[Depends(require_host_or_admin)])
async def assign_workshop_to_slot(
    workshop_id: str,
    assignment: WorkshopSlotAssignmentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Assign a workshop to an event slot (host or admin)."""
    # Verify workshop exists
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Verify event slot exists
    slot = db.query(EventSlot).filter(EventSlot.id == assignment.event_slot_id).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Event slot not found")
    
    # Check if slot is already assigned to another event
    if slot.event_id and slot.event_id != workshop_id:
        raise HTTPException(status_code=409, detail="Event slot is already assigned to another workshop")
    
    # Check if host is available for this slot (if not admin)
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop_id).first()
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host and host.user_id != current_user.id:
            # Check if user is admin
            from models import Admins
            is_admin = db.query(Admins).filter(Admins.user_id == current_user.id).first()
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only the workshop host or admin can assign this workshop")
        
        # Verify host availability for this slot
        if host and host.available_slot_ids and assignment.event_slot_id not in host.available_slot_ids:
            raise HTTPException(status_code=400, detail="Host is not available for this time slot")
    
    # Check for time conflicts with other workshops by the same host
    if host_event:
        conflicting_slots = db.query(EventSlot).filter(
            EventSlot.event_id != workshop_id,
            EventSlot.start_time < slot.end_time,
            EventSlot.end_time > slot.start_time
        ).all()
        
        for conflict_slot in conflicting_slots:
            if conflict_slot.event_id:
                conflicting_host = db.query(HostEvents).filter(
                    HostEvents.event_id == conflict_slot.event_id,
                    HostEvents.host_id == host_event.host_id
                ).first()
                if conflicting_host:
                    raise HTTPException(status_code=409, detail="Host has a time conflict with another workshop")
    
    # Assign workshop to slot
    slot.event_id = workshop_id
    db.commit()
    db.refresh(slot)
    
    return _format_workshop_slot_assignment_response(workshop, slot, db)


@router.delete("/{workshop_id}/unassign-slot/{slot_id}", dependencies=[Depends(require_host_or_admin)])
async def unassign_workshop_from_slot(
    workshop_id: str,
    slot_id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Unassign a workshop from an event slot (host or admin)."""
    # Verify workshop exists
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    # Verify event slot exists and is assigned to this workshop
    slot = db.query(EventSlot).filter(
        EventSlot.id == slot_id,
        EventSlot.event_id == workshop_id
    ).first()
    if not slot:
        raise HTTPException(status_code=404, detail="Event slot not found or not assigned to this workshop")
    
    # Check permissions
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop_id).first()
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host and host.user_id != current_user.id:
            # Check if user is admin
            from models import Admins
            is_admin = db.query(Admins).filter(Admins.user_id == current_user.id).first()
            if not is_admin:
                raise HTTPException(status_code=403, detail="Only the workshop host or admin can unassign this workshop")
    
    # Unassign workshop from slot
    slot.event_id = None
    db.commit()
    
    return {"message": "Workshop unassigned from slot successfully"}


@router.get("/{workshop_id}/slots", response_model=List[dict])
async def get_workshop_slots(workshop_id: str, db: Session = Depends(get_db)):
    """Get all event slots assigned to a workshop (public)."""
    workshop = db.query(Events).filter(Events.id == workshop_id).first()
    if not workshop:
        raise HTTPException(status_code=404, detail="Workshop not found")
    
    slots = db.query(EventSlot).filter(EventSlot.event_id == workshop_id).all()
    result = []
    
    for slot in slots:
        location = db.query(Locations).filter(Locations.id == slot.location_id).first()
        result.append(_format_event_slot_simple(slot, location))
    
    return result


# Helper functions
def _format_workshop_response(workshop: Events, db: Session) -> dict:
    """Format workshop response with all related data."""
    # Get host information
    host_event = db.query(HostEvents).filter(HostEvents.event_id == workshop.id).first()
    host = None
    host_user = None
    if host_event:
        host = db.query(Hosts).filter(Hosts.id == host_event.host_id).first()
        if host:
            host_user = db.query(Users).filter(Users.id == host.user_id).first()
    
    # Get prerequisites
    prerequisites = []
    if workshop.prerequisite_ids:
        for prereq_id in workshop.prerequisite_ids:
            prereq = db.query(Capabilities).filter(Capabilities.id == prereq_id).first()
            if prereq:
                prerequisites.append(_format_prerequisite_simple(prereq))
    
    # Get equipment
    equipment_list = []
    if workshop.equipment_ids:
        for equip_id in workshop.equipment_ids:
            equip = db.query(Equipment).filter(Equipment.id == equip_id).first()
            if equip:
                location = db.query(Locations).filter(Locations.id == equip.location_id).first()
                equipment_list.append(_format_equipment_simple(equip, location))
    
    # Get scheduled event slots
    event_slots = db.query(EventSlot).filter(EventSlot.event_id == workshop.id).all()
    formatted_slots = []
    for slot in event_slots:
        location = db.query(Locations).filter(Locations.id == slot.location_id).first()
        formatted_slots.append(_format_event_slot_simple(slot, location))
    
    # Count current students
    current_students = db.query(Selections).filter(
        Selections.event_id == workshop.id,
        Selections.commitment_level == "committed"
    ).count()
    
    return {
        "id": workshop.id,
        "name": workshop.name,
        "description": workshop.description,
        "host_id": host.id if host else None,
        "host_name": host_user.name if host_user else None,
        "max_students": workshop.max_students,
        "current_students": current_students,
        "prerequisites": prerequisites,
        "equipment": equipment_list,
        "event_slots": formatted_slots,
        "created_at": workshop.created_at.isoformat() if workshop.created_at else None,
        "updated_at": workshop.updated_at.isoformat() if workshop.updated_at else None
    }


def _format_prerequisite_simple(prerequisite: Capabilities) -> dict:
    """Format prerequisite for inclusion in workshop response."""
    # Get all transitive prerequisites
    all_prereqs = []
    if prerequisite.parent_capability_ids:
        all_prereqs = _get_all_prerequisites_simple(prerequisite.id, Session.object_session(prerequisite))
    
    return {
        "id": prerequisite.id,
        "name": prerequisite.name,
        "description": prerequisite.description,
        "parent_prerequisites": [],  # Simplified
        "all_prerequisites": all_prereqs,
        "created_at": prerequisite.created_at.isoformat() if prerequisite.created_at else None,
        "updated_at": prerequisite.updated_at.isoformat() if prerequisite.updated_at else None
    }


def _get_all_prerequisites_simple(prereq_id: str, db: Session) -> List[dict]:
    """Get simplified list of all prerequisites."""
    visited = set()
    result = []
    
    def collect(pid: str):
        if pid in visited:
            return
        visited.add(pid)
        p = db.query(Capabilities).filter(Capabilities.id == pid).first()
        if p and p.parent_capability_ids:
            for parent_id in p.parent_capability_ids:
                parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
                if parent:
                    result.append({"id": parent.id, "name": parent.name, "description": parent.description})
                    collect(parent_id)
    
    collect(prereq_id)
    return result


def _format_equipment_simple(equipment: Equipment, location: Locations) -> dict:
    """Format equipment for inclusion in workshop response."""
    return {
        "id": equipment.id,
        "name": equipment.name,
        "description": equipment.description,
        "location_id": equipment.location_id,
        "location_name": location.name if location else None,
        "quantity": equipment.quantity,
        "created_at": equipment.created_at.isoformat() if equipment.created_at else None,
        "updated_at": equipment.updated_at.isoformat() if equipment.updated_at else None
    }


def _format_event_slot_simple(slot: EventSlot, location: Locations) -> dict:
    """Format event slot for inclusion in workshop response."""
    return {
        "id": slot.id,
        "convention_id": slot.convention_id,
        "start_time": slot.start_time.isoformat(),
        "end_time": slot.end_time.isoformat(),
        "location": {
            "id": location.id if location else None,
            "name": location.name if location else None,
            "description": location.description if location else None,
            "capacity": location.capacity if location else None,
            "address": location.address if location else None,
            "equipment": [],
            "created_at": location.created_at.isoformat() if location and location.created_at else None,
            "updated_at": location.updated_at.isoformat() if location and location.updated_at else None
        },
        "created_at": slot.created_at.isoformat() if slot.created_at else None,
        "updated_at": slot.updated_at.isoformat() if slot.updated_at else None
    }


def _format_host_availability_response(host: Hosts, db: Session) -> dict:
    """Format host availability response."""
    user = db.query(Users).filter(Users.id == host.user_id).first()
    
    # Get available slots
    available_slots = []
    if host.available_slot_ids:
        for slot_id in host.available_slot_ids:
            slot = db.query(EventSlot).filter(EventSlot.id == slot_id).first()
            if slot:
                location = db.query(Locations).filter(Locations.id == slot.location_id).first()
                available_slots.append(_format_event_slot_simple(slot, location))
    
    # Get host's workshops
    host_events = db.query(HostEvents).filter(HostEvents.host_id == host.id).all()
    workshops = []
    for he in host_events:
        workshop = db.query(Events).filter(Events.id == he.event_id).first()
        if workshop:
            workshops.append(_format_workshop_response(workshop, db))
    
    return {
        "host_id": host.id,
        "host_name": user.name if user else None,
        "available_slots": available_slots,
        "workshops": workshops
    }


def _format_workshop_slot_assignment_response(workshop: Events, slot: EventSlot, db: Session) -> dict:
    """Format workshop slot assignment response."""
    location = db.query(Locations).filter(Locations.id == slot.location_id).first()
    
    return {
        "workshop": _format_workshop_response(workshop, db),
        "event_slot": _format_event_slot_simple(slot, location),
        "assigned_at": slot.updated_at.isoformat() if slot.updated_at else None
    }