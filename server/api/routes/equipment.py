"""
Equipment management routes for admin users.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import Equipment, Locations
from api.auth import require_admin
from api.schemas import EquipmentCreate, EquipmentUpdate, EquipmentResponse

router = APIRouter(prefix="/equipment", tags=["equipment"])




@router.post("/", response_model=EquipmentResponse)
async def create_equipment(
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """Add equipment to a location (admin only)."""
    # Verify location exists
    location = db.query(Locations).filter(Locations.id == equipment.location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    new_equipment = Equipment(
        id=str(uuid.uuid4()),
        name=equipment.name,
        description=equipment.description,
        location_id=equipment.location_id,
        quantity=equipment.quantity,
        convention_id=location.convention_id
    )
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    return _format_equipment_response(new_equipment, location)


@router.get("/", response_model=List[EquipmentResponse])
async def list_equipment(
    location_id: Optional[str] = Query(None, description="Filter by location"),
    convention_id: Optional[str] = Query(None, description="Filter by convention"),
    db: Session = Depends(get_db)
):
    """List equipment (public), optionally filtered by location or convention."""
    query = db.query(Equipment)
    
    if location_id:
        query = query.filter(Equipment.location_id == location_id)
    if convention_id:
        query = query.filter(Equipment.convention_id == convention_id)
    
    equipment_list = query.all()
    result = []
    
    for equipment in equipment_list:
        location = db.query(Locations).filter(Locations.id == equipment.location_id).first()
        result.append(_format_equipment_response(equipment, location))
    
    return result


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(equipment_id: str, db: Session = Depends(get_db)):
    """Get equipment details (public)."""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    location = db.query(Locations).filter(Locations.id == equipment.location_id).first()
    return _format_equipment_response(equipment, location)


@router.put("/{equipment_id}", response_model=EquipmentResponse, dependencies=[Depends(require_admin)])
async def update_equipment(
    equipment_id: str,
    update: EquipmentUpdate,
    db: Session = Depends(get_db)
):
    """Update equipment details (admin only)."""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    if update.name is not None:
        equipment.name = update.name
    if update.description is not None:
        equipment.description = update.description
    if update.quantity is not None:
        if update.quantity < 1:
            raise HTTPException(status_code=400, detail="Quantity must be at least 1")
        equipment.quantity = update.quantity
    if update.location_id is not None:
        location = db.query(Locations).filter(Locations.id == update.location_id).first()
        if not location:
            raise HTTPException(status_code=404, detail="Location not found")
        equipment.location_id = update.location_id
        equipment.convention_id = location.convention_id
    
    db.commit()
    db.refresh(equipment)
    
    location = db.query(Locations).filter(Locations.id == equipment.location_id).first()
    return _format_equipment_response(equipment, location)


@router.delete("/{equipment_id}", dependencies=[Depends(require_admin)])
async def delete_equipment(equipment_id: str, db: Session = Depends(get_db)):
    """Delete equipment (admin only)."""
    equipment = db.query(Equipment).filter(Equipment.id == equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    
    db.delete(equipment)
    db.commit()
    
    return {"message": "Equipment deleted successfully"}


@router.post("/locations/{location_id}/equipment", response_model=EquipmentResponse, dependencies=[Depends(require_admin)])
async def add_equipment_to_location(
    location_id: str,
    equipment: EquipmentCreate,
    db: Session = Depends(get_db)
):
    """Add equipment directly to a specific location (admin only)."""
    location = db.query(Locations).filter(Locations.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Override the location_id from the request body
    new_equipment = Equipment(
        id=str(uuid.uuid4()),
        name=equipment.name,
        description=equipment.description,
        location_id=location_id,
        quantity=equipment.quantity,
        convention_id=location.convention_id
    )
    db.add(new_equipment)
    db.commit()
    db.refresh(new_equipment)
    
    return _format_equipment_response(new_equipment, location)


@router.get("/locations/{location_id}/equipment", response_model=List[EquipmentResponse])
async def list_location_equipment(location_id: str, db: Session = Depends(get_db)):
    """List all equipment at a specific location (public)."""
    location = db.query(Locations).filter(Locations.id == location_id).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    equipment_list = db.query(Equipment).filter(Equipment.location_id == location_id).all()
    
    return [_format_equipment_response(e, location) for e in equipment_list]


# Helper function
def _format_equipment_response(equipment: Equipment, location: Optional[Locations]) -> dict:
    """Format equipment response with location information."""
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