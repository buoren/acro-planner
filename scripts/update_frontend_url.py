#!/usr/bin/env python3
"""
Script to update the frontend URL in the database using gcloud credentials.
This script starts cloud-sql-proxy and connects through it.
"""

import os
import sys
import uuid
import subprocess
import time
import socket
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

def check_port_available(host='127.0.0.1', port=3306):
    """Check if a port is available."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result != 0  # Returns True if port is available (connection failed)

def wait_for_port(host='127.0.0.1', port=3306, timeout=30):
    """Wait for a port to become accessible."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        if result == 0:  # Port is open
            return True
        time.sleep(1)
    return False

def start_cloud_sql_proxy():
    """Start cloud-sql-proxy and wait for it to be ready."""
    connection_name = "acro-session-planner:us-central1:acro-planner-mysql"
    port = 3306
    
    # Check if port is already in use
    if not check_port_available('127.0.0.1', port):
        print(f"⚠️  Port {port} is already in use. Trying to kill existing proxy...")
        # Try to kill any existing cloud-sql-proxy processes
        subprocess.run(["pkill", "-f", "cloud-sql-proxy"], capture_output=True)
        time.sleep(2)
        
        # Check again
        if not check_port_available('127.0.0.1', port):
            print(f"❌ Port {port} is still in use. Cannot start cloud-sql-proxy.")
            return None
    
    print(f"🔌 Starting cloud-sql-proxy for {connection_name} on port {port}...")
    
    try:
        # Start cloud-sql-proxy in the background
        proxy_process = subprocess.Popen([
            "cloud-sql-proxy", 
            f"--port={port}",
            connection_name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for the proxy to be ready
        print("⏳ Waiting for cloud-sql-proxy to be ready...")
        if wait_for_port('127.0.0.1', port, timeout=30):
            print("✅ Cloud SQL proxy is ready and accepting connections")
            return proxy_process
        else:
            print("❌ Cloud SQL proxy failed to become ready within 30 seconds")
            proxy_process.terminate()
            proxy_process.wait()
            return None
            
    except FileNotFoundError:
        print("❌ cloud-sql-proxy not found. Please install: gcloud components install cloud_sql_proxy")
        return None
    except Exception as e:
        print(f"❌ Error starting cloud-sql-proxy: {e}")
        return None

def get_database_password():
    """Get database password from Secret Manager."""
    try:
        result = subprocess.run([
            "gcloud", "secrets", "versions", "access", "latest", 
            "--secret=acro-planner-mysql-password", "--project=acro-session-planner"
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get database password from Secret Manager: {e}")
        print(f"   stderr: {e.stderr}")
        return None

def update_frontend_url(frontend_url):
    """Update the frontend URL in the system_settings table."""
    try:
        # Get database password
        db_password = get_database_password()
        if not db_password:
            return False
        
        # Build database URL
        db_user = "acro_user"
        db_name = "acro_planner"
        database_url = f"mysql+pymysql://{db_user}:{db_password}@127.0.0.1:3306/{db_name}"
        
        print(f"🔄 Updating frontend URL in database: {frontend_url}")
        print(f"📊 Connecting to database...")
        
        # Create engine with connection pooling
        engine = create_engine(
            database_url, 
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # Test connection first
        print("🔧 Testing database connection...")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            print("✅ Database connection successful")
        
        # Now update the setting
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        setting_id = str(uuid.uuid4())
        setting_name = "frontend_url"
        description = "URL of the deployed Flutter frontend application"
        now = datetime.now()
        
        # Check if setting already exists
        result = db.execute(
            text("SELECT id FROM system_settings WHERE name = :name"),
            {"name": setting_name}
        ).fetchone()
        
        if result:
            # Update existing setting
            db.execute(
                text("""
                    UPDATE system_settings 
                    SET value = :value, description = :description, updated_at = :updated_at
                    WHERE name = :name
                """),
                {
                    "value": frontend_url,
                    "description": description,
                    "updated_at": now,
                    "name": setting_name
                }
            )
            print(f"✅ Updated existing frontend_url setting to: {frontend_url}")
        else:
            # Insert new setting
            db.execute(
                text("""
                    INSERT INTO system_settings (id, name, value, description, created_at, updated_at)
                    VALUES (:id, :name, :value, :description, :created_at, :updated_at)
                """),
                {
                    "id": setting_id,
                    "name": setting_name,
                    "value": frontend_url,
                    "description": description,
                    "created_at": now,
                    "updated_at": now
                }
            )
            print(f"✅ Created new frontend_url setting: {frontend_url}")
        
        db.commit()
        db.close()
        engine.dispose()
        return True
        
    except Exception as e:
        print(f"❌ Error updating frontend URL in database: {str(e)}")
        return False

def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python update_frontend_url.py <frontend_url>")
        sys.exit(1)
    
    frontend_url = sys.argv[1]
    proxy_process = None
    
    try:
        # Start cloud-sql-proxy
        proxy_process = start_cloud_sql_proxy()
        
        if proxy_process is None:
            print("❌ Failed to start cloud-sql-proxy")
            sys.exit(1)
        
        # Update the frontend URL
        if update_frontend_url(frontend_url):
            print("🎉 Frontend URL updated successfully!")
            exit_code = 0
        else:
            print("💥 Failed to update frontend URL")
            exit_code = 1
            
    finally:
        # Clean up proxy process
        if proxy_process:
            print("🔌 Stopping cloud-sql-proxy...")
            proxy_process.terminate()
            proxy_process.wait()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()