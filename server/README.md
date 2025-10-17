# Acro Planner Backend Server

FastAPI backend server for the Acro Planner application, configured for deployment to Google Cloud with MySQL.

## Setup

1. Install dependencies:
```bash
cd server
poetry install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

## Run Development Server

```bash
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will run at http://localhost:8000

## API Endpoints

- `GET /` - Hello World endpoint
- `GET /health` - Health check endpoint

## Database Configuration

The server is configured to connect to MySQL. For Google Cloud SQL, use the connection string format:
```
mysql+pymysql://user:password@/database_name?unix_socket=/cloudsql/project:region:instance
```

The server will run without a database connection for testing purposes.