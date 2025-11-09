"""
System settings utilities for managing configuration.
"""

import uuid
from typing import Optional
from sqlalchemy.orm import Session
from models import SystemSetting


def get_system_setting(db: Session, name: str, default_value: Optional[str] = None) -> Optional[str]:
    """
    Get a system setting value by name.
    
    Args:
        db: Database session
        name: Setting name
        default_value: Default value if setting doesn't exist
        
    Returns:
        Setting value or default_value if not found
    """
    setting = db.query(SystemSetting).filter(SystemSetting.name == name).first()
    if setting:
        return setting.value
    return default_value


def set_system_setting(db: Session, name: str, value: str, description: Optional[str] = None) -> SystemSetting:
    """
    Set a system setting value (create or update).
    
    Args:
        db: Database session
        name: Setting name
        value: Setting value
        description: Optional description
        
    Returns:
        SystemSetting instance
    """
    setting = db.query(SystemSetting).filter(SystemSetting.name == name).first()
    
    if setting:
        # Update existing setting
        setting.value = value
        if description is not None:
            setting.description = description
    else:
        # Create new setting
        setting = SystemSetting(
            id=str(uuid.uuid4()),
            name=name,
            value=value,
            description=description
        )
        db.add(setting)
    
    db.commit()
    db.refresh(setting)
    return setting


def delete_system_setting(db: Session, name: str) -> bool:
    """
    Delete a system setting.
    
    Args:
        db: Database session
        name: Setting name
        
    Returns:
        True if setting was deleted, False if not found
    """
    setting = db.query(SystemSetting).filter(SystemSetting.name == name).first()
    if setting:
        db.delete(setting)
        db.commit()
        return True
    return False


def get_frontend_url(db: Session) -> str:
    """
    Get the frontend URL from system settings with fallback.
    
    Args:
        db: Database session
        
    Returns:
        Frontend URL
    """
    # Try to get from database first
    frontend_url = get_system_setting(
        db, 
        "frontend_url", 
        "https://storage.googleapis.com/acro-planner-flutter-app-733697808355/release_20251109_154514/index.html"
    )
    
    return frontend_url