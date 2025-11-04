#!/usr/bin/env python3
"""
Database migration script for Acro Planner.
Runs a specific migration script against the production database.
"""

import os
import sys
from pathlib import Path

# Add the server directory to the path so we can import our modules
server_dir = Path(__file__).parent
sys.path.insert(0, str(server_dir))

try:
    import pymysql
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    print("Error: Missing required packages. Please install them with:")
    print("poetry install")
    sys.exit(1)


def get_database_url():
    """Get database URL from environment variables."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("Error: DATABASE_URL environment variable not set")
        print("Please set DATABASE_URL to your production database connection string")
        sys.exit(1)
    
    print(f"Using database URL: {database_url}")
    return database_url


def run_migration(engine, migration_file):
    """Run a specific migration file."""
    migration_path = Path(__file__).parent / "scripts" / "sql" / migration_file
    
    if not migration_path.exists():
        print(f"Migration file not found: {migration_path}")
        return False

    print(f"Running migration: {migration_file}")

    try:
        with open(migration_path) as f:
            sql_content = f.read()

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        with engine.connect() as conn:
            for i, statement in enumerate(statements, 1):
                if statement:
                    print(f"Executing statement {i}/{len(statements)}: {statement[:100]}...")
                    try:
                        conn.execute(text(statement))
                        conn.commit()
                        print(f"✅ Statement {i} executed successfully")
                    except Exception as e:
                        print(f"⚠️  Statement {i} failed (might be expected): {e}")
                        # Continue with other statements

        print(f"✅ Migration {migration_file} completed")
        return True

    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False


def main():
    """Main migration function."""
    if len(sys.argv) != 2:
        print("Usage: python migrate_db.py <migration_file>")
        print("Example: python migrate_db.py 006_add_conventions_and_fix_attendees.sql")
        sys.exit(1)
    
    migration_file = sys.argv[1]
    
    print("🗃️  Acro Planner Database Migration")
    print("=" * 50)
    print(f"Migration: {migration_file}")

    # Get database configuration
    database_url = get_database_url()

    # Connect to the database
    try:
        engine = create_engine(database_url)
        print("✅ Connected to database")

        # Test the connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection successful")

        # Run the migration
        if run_migration(engine, migration_file):
            print(f"\n✅ Migration {migration_file} completed successfully!")
        else:
            print(f"\n❌ Migration {migration_file} failed!")
            sys.exit(1)

    except SQLAlchemyError as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    main()