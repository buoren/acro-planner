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
    Get the frontend URL from system settings, with dynamic discovery fallback.
    
    Args:
        db: Database session
        
    Returns:
        Frontend URL
    """
    # Try to get from database first
    frontend_url = get_system_setting(db, "frontend_url")
    
    if frontend_url:
        return frontend_url
    
    # If not in database, try to discover the latest release dynamically
    try:
        import subprocess
        import re
        
        # Query Google Cloud Storage to find the latest release
        result = subprocess.run([
            'gsutil', 'ls', 'gs://acro-planner-flutter-app-733697808355/'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Find all release directories
            release_dirs = []
            for line in result.stdout.strip().split('\n'):
                if 'release_' in line and line.endswith('/'):
                    # Extract release timestamp for sorting
                    match = re.search(r'release_(\d{8}_\d{6})/', line)
                    if match:
                        timestamp = match.group(1)
                        release_dirs.append((timestamp, line.rstrip('/')))
            
            if release_dirs:
                # Sort by timestamp and get the latest
                release_dirs.sort(reverse=True)
                latest_release_path = release_dirs[0][1]
                latest_frontend_url = f"{latest_release_path}/index.html"
                
                # Store in database for future use
                set_system_setting(
                    db, 
                    "frontend_url", 
                    latest_frontend_url, 
                    "Automatically discovered frontend URL"
                )
                
                return latest_frontend_url
    
    except Exception as e:
        # Log the error but continue with fallback
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to auto-discover frontend URL: {e}")
    
    # Ultimate fallback - this should rarely be used
    fallback_url = "https://storage.googleapis.com/acro-planner-flutter-app-733697808355/release_20251109_212234/index.html"
    
    # Store the fallback in database so we don't keep hitting this code path
    set_system_setting(
        db, 
        "frontend_url", 
        fallback_url, 
        "Fallback frontend URL - should be updated with actual latest release"
    )
    
    return fallback_url