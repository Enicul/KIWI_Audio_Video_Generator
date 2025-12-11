FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml ./
COPY kiwi_video ./kiwi_video
COPY config ./config

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Create workspace directory
RUN mkdir -p /app/workspaces

# Expose API port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV WORKSPACE_DIR=/app/workspaces

# Run the application
CMD ["uvicorn", "kiwi_video.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

