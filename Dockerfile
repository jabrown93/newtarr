# Build stage: install dependencies using the dev image (has shell + tools)
FROM dhi.io/python:3.14.3-dev AS builder

WORKDIR /app

# Install required packages from the root requirements file
COPY requirements.txt /app/
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Prepare /config directory tree with correct ownership and permissions
RUN mkdir -p /config/settings /config/stateful /config/user /config/logs && \
    chown -R 1000:1000 /config && \
    chmod -R 700 /config

# Final stage: minimal runtime image
FROM dhi.io/python:3.14.3

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Copy pre-created config directory with correct ownership
COPY --from=builder --chown=65532:65532 /config /config

# Copy application code
COPY . /app/

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 9705

# Health check using the existing /api/health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:9705/ping')" || exit 1

# Run the main application using the new entry point
CMD ["python3", "main.py"]
