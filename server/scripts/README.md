# Database Initialization Scripts

This directory contains scripts to initialize the Acro Planner database from scratch using SQL commands.

## Files

- `init_db.py` - Main Python script that connects to the database and runs SQL files
- `init_db.sh` - Shell wrapper script (for local convenience)
- `sql/` - Directory containing SQL scripts that will be executed in order:
  - `001_create_tables.sql` - Table creation statements
  - `002_create_indexes.sql` - Index creation statements  
  - `003_insert_seed_data.sql` - Initial/seed data

## Running with Cloud SQL

### Prerequisites

1. Cloud SQL proxy installed:
   ```bash
   curl -o cloud-sql-proxy https://storage.googleapis.com/cloud-sql-connectors/cloud-sql-proxy/v2.8.0/cloud-sql-proxy.darwin.amd64
   chmod +x cloud-sql-proxy
   sudo mv cloud-sql-proxy /usr/local/bin/
   ```

2. Authenticate with gcloud:
   ```bash
   gcloud auth application-default login
   ```

### Method 1: Using Cloud SQL Proxy (Recommended)

1. Start the Cloud SQL proxy:
   ```bash
   cloud-sql-proxy acro-session-planner:us-central1:acro-planner-db --port 3306
   ```

2. Set environment variables for local connection:
   ```bash
   export DB_HOST=127.0.0.1
   export DB_PORT=3306
   export DB_USER=root
   export DB_PASSWORD=your_cloud_sql_password
   export DB_NAME=acro_planner
   ```

3. Run the initialization script:
   ```bash
   cd /path/to/server
   poetry run python scripts/init_db.py
   ```

### Method 2: Direct Cloud SQL Connection

Set the full DATABASE_URL environment variable:
```bash
export DATABASE_URL="mysql+pymysql://root:your_password@127.0.0.1:3306/acro_planner"
poetry run python scripts/init_db.py
```

### Method 3: Using Production Cloud SQL Connection String

For direct connection (less secure, not recommended for production):
```bash
export DATABASE_URL="mysql+pymysql://root:password@/acro_planner?unix_socket=/cloudsql/acro-session-planner:us-central1:acro-planner-db"
```

## What the Script Does

1. **Creates database** if it doesn't exist
2. **Connects** to the specified database
3. **Runs SQL files** in order:
   - Creates all tables
   - Creates indexes for performance
   - Inserts seed/initial data
4. **Provides feedback** on success/failure

## Customizing the Schema

1. Edit `sql/001_create_tables.sql` with your table definitions
2. Edit `sql/002_create_indexes.sql` with your index definitions  
3. Edit `sql/003_insert_seed_data.sql` with your initial data
4. Run the script to apply changes

## Example Usage

```bash
# Start Cloud SQL proxy in one terminal
cloud-sql-proxy acro-session-planner:us-central1:acro-planner-db --port 3306

# In another terminal, set environment and run script
export DB_HOST=127.0.0.1
export DB_USER=root
export DB_PASSWORD=your_cloud_sql_password
export DB_NAME=acro_planner

cd /Users/buoren/repos/acro-planner/server
poetry run python scripts/init_db.py
```

## Troubleshooting

- **Connection refused**: Make sure Cloud SQL proxy is running
- **Authentication failed**: Check your Cloud SQL password
- **Database not found**: The script will create it automatically
- **Permission denied**: Ensure your user has CREATE DATABASE privileges