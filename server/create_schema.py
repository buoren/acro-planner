#!/usr/bin/env python3
"""
Schema creation script for Acro Planner.
Uses SQLAlchemy to create all tables defined in models.py
"""

import os
import sys
from pathlib import Path

# Add the server directory to the path so we can import our modules
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

try:
    from sqlalchemy import create_engine
    from sqlalchemy.exc import SQLAlchemyError
    from database import Base
    from models import *  # Import all models
except ImportError as e:
    print(f"Error: Missing required packages: {e}")
    print("Please install them with: poetry install")
    sys.exit(1)


def get_database_url():
    """Get database URL for Cloud SQL connection."""
    # For Cloud Run deployment, use the Cloud SQL connection
    connection_name = "acro-session-planner:us-central1:acro-planner-mysql"
    database_url = f"mysql+pymysql://root@/{os.getenv('DB_NAME', 'acro_planner')}?unix_socket=/cloudsql/{connection_name}"
    
    print(f"Using Cloud SQL connection: {database_url}")
    return database_url


def main():
    """Main schema creation function."""
    print("🗃️  Acro Planner Schema Creation")
    print("=" * 50)

    # Get database configuration
    database_url = get_database_url()

    # Connect to the database and create all tables
    try:
        engine = create_engine(database_url)
        print("✅ Connected to database")

        # Create all tables
        print("🔨 Creating all tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # List created tables
        print("\n📋 Tables in database:")
        with engine.connect() as conn:
            result = conn.execute("SHOW TABLES")
            tables = [row[0] for row in result.fetchall()]
            for table in sorted(tables):
                print(f"  - {table}")

        print(f"\n✅ Schema creation completed successfully!")

    except SQLAlchemyError as e:
        print(f"❌ Database operation failed: {e}")
        sys.exit(1)

    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    main()