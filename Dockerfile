FROM dhi.io/python:3.14.3

WORKDIR /app

# Install system dependencies including net-tools for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install required packages from the root requirements file
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app/

# Create non-root user
RUN groupadd -g 1000 newtarr && \
    useradd -u 1000 -g newtarr -s /bin/sh -M newtarr

# Create necessary directories with owner-only permissions
RUN mkdir -p /config/settings /config/stateful /config/user /config/logs && \
    chown -R newtarr:newtarr /config && \
    chmod -R 700 /config

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 9705

# Health check using the existing /api/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:9705/api/health')" || exit 1

# Run as non-root user
USER newtarr

# Run the main application using the new entry point
CMD ["python3", "main.py"]
