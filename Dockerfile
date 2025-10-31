# Dify Terminal Runner Plugin - Docker Image
# Python code execution sandbox for Dify workflows

FROM python:3.11-slim

# Metadata
LABEL maintainer="DaddyTech"
LABEL version="0.2.0"
LABEL description="Dify Terminal Runner Plugin - Secure Python code execution sandbox"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    SESSIONS_DIR=/app/sessions

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Create sessions directory
RUN mkdir -p /app/sessions && chmod 777 /app/sessions

# Copy requirements first (for better layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY executor.py .
COPY manifest.json .

# Create non-root user for security (optional, can be enabled in production)
# RUN useradd -m -u 1000 pluginuser && chown -R pluginuser:pluginuser /app
# USER pluginuser

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

# Default command - run tests
CMD ["python", "main.py"]
