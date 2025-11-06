# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for MySQL client
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install dependencies using pip
RUN pip install --no-cache-dir \
    fastapi==0.119.0 \
    "uvicorn[standard]==0.37.0" \
    sqlalchemy==2.0.44 \
    pymysql==1.1.2 \
    python-dotenv==1.1.1 \
    ulid-py==1.1.0 \
    "pydantic[email]==2.10.3" \
    passlib==1.7.4 \
    cryptography==46.0.3 \
    authlib==1.3.2 \
    requests==2.32.3 \
    itsdangerous==2.2.0 \
    httpx==0.27.2 \
    fastapi-login==1.10.3

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check temporarily disabled for troubleshooting
# HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
#     CMD curl -f http://localhost:8080/health || exit 1

# Run the application
# Google Cloud Run expects port 8080 by default
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]