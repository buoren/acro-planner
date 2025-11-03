#!/usr/bin/env python3
"""
Database initialization script for Acro Planner.
Creates the database from scratch using SQL commands.
"""

import os
import sys
from pathlib import Path

# Add the server directory to the path so we can import our modules
server_dir = Path(__file__).parent.parent
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
    """Get database URL from environment variables or use local default."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        print(f"Using database URL from environment: {database_url}")
        return database_url

    # Local development defaults
    local_config = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "3306"),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "acro_planner")
    }

    # Create database URL
    if local_config["password"]:
        auth = f"{local_config['user']}:{local_config['password']}"
    else:
        auth = local_config["user"]

    database_url = f"mysql+pymysql://{auth}@{local_config['host']}:{local_config['port']}/{local_config['database']}"
    print(f"Using local database configuration: {database_url}")
    return database_url


def create_database_if_not_exists(database_url, db_name):
    """Create the database if it doesn't exist."""
    # Connect without specifying database to create it
    base_url = database_url.rsplit('/', 1)[0]

    try:
        engine = create_engine(base_url)
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SHOW DATABASES LIKE '{db_name}'"))
            if not result.fetchone():
                print(f"Creating database '{db_name}'...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                conn.commit()
                print(f"Database '{db_name}' created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
        engine.dispose()
    except SQLAlchemyError as e:
        print(f"Error creating database: {e}")
        sys.exit(1)


def run_sql_script(engine, script_path):
    """Run SQL commands from a file."""
    if not script_path.exists():
        print(f"SQL script not found: {script_path}")
        return False

    print(f"Running SQL script: {script_path}")

    try:
        with open(script_path) as f:
            sql_content = f.read()

        # Split by semicolon and execute each statement
        statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]

        with engine.connect() as conn:
            for statement in statements:
                if statement:
                    print(f"Executing: {statement[:50]}...")
                    conn.execute(text(statement))
            conn.commit()

        print(f"Successfully executed {len(statements)} SQL statements")
        return True

    except Exception as e:
        print(f"Error running SQL script: {e}")
        return False


def main():
    """Main initialization function."""
    print("🤸‍♀️ Acro Planner Database Initialization")
    print("=" * 50)

    # Get database configuration
    database_url = get_database_url()
    db_name = database_url.split('/')[-1].split('?')[0]

    # Create database if it doesn't exist
    create_database_if_not_exists(database_url, db_name)

    # Connect to the database
    try:
        engine = create_engine(database_url)
        print(f"Connected to database: {db_name}")

        # Test the connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            if result.fetchone():
                print("✅ Database connection successful!")

        # Run SQL scripts in order
        scripts_dir = Path(__file__).parent / "sql"

        # List of SQL scripts to run in order
        sql_scripts = [
            "001_create_tables.sql",
            "002_create_indexes.sql",
            "003_insert_seed_data.sql"
        ]

        scripts_dir.mkdir(exist_ok=True)

        for script_name in sql_scripts:
            script_path = scripts_dir / script_name
            if script_path.exists():
                if not run_sql_script(engine, script_path):
                    print(f"❌ Failed to run {script_name}")
                    sys.exit(1)
            else:
                print(f"⚠️  SQL script not found: {script_name} (skipping)")

        print("\n✅ Database initialization completed successfully!")
        print(f"Database: {db_name}")
        print(f"URL: {database_url}")

    except SQLAlchemyError as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    finally:
        if 'engine' in locals():
            engine.dispose()


if __name__ == "__main__":
    main()
