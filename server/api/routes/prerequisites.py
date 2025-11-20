"""
Prerequisites management routes.
"""

from typing import List, Set
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from database import get_db
from models import Capabilities
from api.auth import require_admin, require_host_or_admin
from api.schemas import PrerequisiteCreate, PrerequisiteUpdate, PrerequisiteResponse

router = APIRouter(prefix="/prerequisites", tags=["prerequisites"])


@router.get("/", response_model=List[PrerequisiteResponse])
async def list_prerequisites(db: Session = Depends(get_db)):
    """List all prerequisites/capabilities (public)."""
    capabilities = db.query(Capabilities).all()
    return [_format_prerequisite_response(cap, db) for cap in capabilities]


@router.post("/", response_model=PrerequisiteResponse, dependencies=[Depends(require_admin)])
async def create_prerequisite(
    prerequisite: PrerequisiteCreate,
    db: Session = Depends(get_db)
):
    """Create a new prerequisite (admin only)."""
    # Verify parent prerequisites exist
    for parent_id in prerequisite.parent_prerequisite_ids:
        parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
        if not parent:
            raise HTTPException(status_code=404, detail=f"Parent prerequisite {parent_id} not found")
    
    new_prerequisite = Capabilities(
        id=str(uuid.uuid4()),
        name=prerequisite.name,
        description=prerequisite.description,
        parent_capability_ids=prerequisite.parent_prerequisite_ids
    )
    db.add(new_prerequisite)
    db.commit()
    db.refresh(new_prerequisite)
    
    return _format_prerequisite_response(new_prerequisite, db)




@router.get("/{prerequisite_id}", response_model=PrerequisiteResponse)
async def get_prerequisite(prerequisite_id: str, db: Session = Depends(get_db)):
    """Get prerequisite details (public)."""
    prerequisite = db.query(Capabilities).filter(Capabilities.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    
    return _format_prerequisite_response(prerequisite, db)


@router.put("/{prerequisite_id}", response_model=PrerequisiteResponse, dependencies=[Depends(require_admin)])
async def update_prerequisite(
    prerequisite_id: str,
    update: PrerequisiteUpdate,
    db: Session = Depends(get_db)
):
    """Update prerequisite details (admin only)."""
    prerequisite = db.query(Capabilities).filter(Capabilities.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    
    if update.name is not None:
        prerequisite.name = update.name
    if update.description is not None:
        prerequisite.description = update.description
    if update.parent_prerequisite_ids is not None:
        # Check for circular dependencies
        if prerequisite_id in update.parent_prerequisite_ids:
            raise HTTPException(status_code=400, detail="A prerequisite cannot depend on itself")
        
        # Verify parent prerequisites exist and check for circular dependencies
        for parent_id in update.parent_prerequisite_ids:
            parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail=f"Parent prerequisite {parent_id} not found")
            
            # Check if adding this parent would create a cycle
            if _would_create_cycle(prerequisite_id, parent_id, db):
                raise HTTPException(
                    status_code=400,
                    detail=f"Adding {parent_id} as parent would create a circular dependency"
                )
        
        prerequisite.parent_capability_ids = update.parent_prerequisite_ids
    
    db.commit()
    db.refresh(prerequisite)
    
    return _format_prerequisite_response(prerequisite, db)


@router.delete("/{prerequisite_id}", dependencies=[Depends(require_admin)])
async def delete_prerequisite(prerequisite_id: str, db: Session = Depends(get_db)):
    """Delete a prerequisite (admin only)."""
    prerequisite = db.query(Capabilities).filter(Capabilities.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    
    # Check if any other prerequisites depend on this one
    dependent = db.query(Capabilities).filter(
        Capabilities.parent_capability_ids.contains([prerequisite_id])
    ).first()
    if dependent:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete prerequisite that others depend on"
        )
    
    db.delete(prerequisite)
    db.commit()
    
    return {"message": "Prerequisite deleted successfully"}


@router.post("/{prerequisite_id}/add-parent", response_model=PrerequisiteResponse, dependencies=[Depends(require_host_or_admin)])
async def add_parent_prerequisite(
    prerequisite_id: str,
    parent_id: str,
    db: Session = Depends(get_db)
):
    """Add a parent prerequisite to an existing one (host or admin)."""
    prerequisite = db.query(Capabilities).filter(Capabilities.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Prerequisite not found")
    
    parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent prerequisite not found")
    
    # Check for circular dependencies
    if prerequisite_id == parent_id:
        raise HTTPException(status_code=400, detail="A prerequisite cannot depend on itself")
    
    if _would_create_cycle(prerequisite_id, parent_id, db):
        raise HTTPException(
            status_code=400,
            detail="Adding this parent would create a circular dependency"
        )
    
    # Add parent if not already present
    parent_ids = prerequisite.parent_capability_ids or []
    if parent_id not in parent_ids:
        parent_ids.append(parent_id)
        prerequisite.parent_capability_ids = parent_ids
        db.commit()
        db.refresh(prerequisite)
    
    return _format_prerequisite_response(prerequisite, db)


# Helper functions
def _would_create_cycle(child_id: str, potential_parent_id: str, db: Session) -> bool:
    """Check if adding a parent would create a circular dependency."""
    visited = set()
    
    def has_path(from_id: str, to_id: str) -> bool:
        if from_id == to_id:
            return True
        if from_id in visited:
            return False
        visited.add(from_id)
        
        prerequisite = db.query(Capabilities).filter(Capabilities.id == from_id).first()
        if not prerequisite or not prerequisite.parent_capability_ids:
            return False
        
        for parent_id in prerequisite.parent_capability_ids:
            if has_path(parent_id, to_id):
                return True
        return False
    
    # Check if potential_parent can reach child (which would create a cycle)
    return has_path(potential_parent_id, child_id)


def _get_all_prerequisites(prerequisite_id: str, db: Session) -> List[dict]:
    """Recursively get all prerequisites (including transitive ones)."""
    visited = set()
    result = []
    
    def collect_prerequisites(prereq_id: str):
        if prereq_id in visited:
            return
        visited.add(prereq_id)
        
        prerequisite = db.query(Capabilities).filter(Capabilities.id == prereq_id).first()
        if not prerequisite or not prerequisite.parent_capability_ids:
            return
        
        for parent_id in prerequisite.parent_capability_ids:
            parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
            if parent:
                result.append({
                    "id": parent.id,
                    "name": parent.name,
                    "description": parent.description
                })
                collect_prerequisites(parent_id)
    
    collect_prerequisites(prerequisite_id)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_result = []
    for item in result:
        if item["id"] not in seen:
            seen.add(item["id"])
            unique_result.append(item)
    
    return unique_result


def _format_prerequisite_response(prerequisite: Capabilities, db: Session) -> dict:
    """Format prerequisite response with parent and all transitive prerequisites."""
    parent_prerequisites = []
    if prerequisite.parent_capability_ids:
        for parent_id in prerequisite.parent_capability_ids:
            parent = db.query(Capabilities).filter(Capabilities.id == parent_id).first()
            if parent:
                parent_prerequisites.append({
                    "id": parent.id,
                    "name": parent.name,
                    "description": parent.description
                })
    
    all_prerequisites = _get_all_prerequisites(prerequisite.id, db)
    
    return {
        "id": prerequisite.id,
        "name": prerequisite.name,
        "description": prerequisite.description,
        "parent_prerequisites": parent_prerequisites,
        "all_prerequisites": all_prerequisites,
        "created_at": prerequisite.created_at.isoformat() if prerequisite.created_at else None,
        "updated_at": prerequisite.updated_at.isoformat() if prerequisite.updated_at else None
    }