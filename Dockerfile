# Dockerfile

# --- Build Stage ---
# Use a slim Python image as a builder to compile dependencies.
FROM python:3.11-slim as builder

WORKDIR /app

# Install build-time dependencies needed for some Python packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file to leverage Docker's build cache.
COPY requirements.txt .
# Install Python packages.
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt 

# --- Production Stage ---
# Start from a fresh slim image for a smaller final image size.
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies like curl, which is needed for the health check.
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a dedicated, non-root user for security.
RUN useradd --create-home --shell /bin/bash appuser

# Copy the installed Python packages from the builder stage.
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code into the container. 
COPY . .
# Create log directories and give the non-root user ownership of the app directory.
RUN mkdir -p logs && \
    chown -R appuser:appuser /app 

# Switch to the non-root user.
USER appuser

# Expose the port the application will run on.
EXPOSE 5000

# Set environment variables for production.
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production

# Define a health check to ensure the container is running properly.
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1 

# The command to run the application using a production-grade ASGI server.
CMD ["hypercorn", "--workers", "4", "--bind", "0.0.0.0:5000", "run:app"]