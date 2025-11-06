#!/usr/bin/env python3
"""
Migration script to create the password_reset table.

Run this script to create the password_reset table in your database.
Usage: python migrations/create_password_reset_table.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import models
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, inspect
from models import PasswordReset, Base
from database import engine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_password_reset_table():
    """Create the password_reset table if it doesn't exist."""
    
    inspector = inspect(engine)
    
    # Check if table already exists
    if 'password_reset' in inspector.get_table_names():
        print("❌ Table 'password_reset' already exists. Skipping creation.")
        return False
    
    # Create the table
    print("🔨 Creating 'password_reset' table...")
    
    # Create only the password_reset table
    PasswordReset.__table__.create(bind=engine, checkfirst=True)
    
    print("✅ Table 'password_reset' created successfully!")
    return True


if __name__ == "__main__":
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            print("⚠️  Warning: DATABASE_URL not set. Table will be created when the app starts with a database connection.")
            print("💡 To create the table now, set DATABASE_URL in your environment or .env file.")
            sys.exit(0)
        
        created = create_password_reset_table()
        
        if created:
            print("\n📝 Password Reset Table Schema:")
            print("  - id: String(36) - Primary key (ULID)")
            print("  - user_id: String(36) - Foreign key to users table")
            print("  - temporary_password_hash: String(255) - Hashed temporary password")
            print("  - salt: String(255) - Salt for the password hash")
            print("  - created_at: DateTime - Timestamp of creation")
            print("  - is_consumed: Boolean - Whether the reset has been used")
            
    except Exception as e:
        print(f"❌ Error creating table: {str(e)}")
        sys.exit(1)