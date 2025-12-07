# Geant4 API Docker Image
# =======================
# Multi-stage build for production deployment

# Stage 1: Base with Geant4
FROM ubuntu:22.04 AS geant4-base

ENV DEBIAN_FRONTEND=noninteractive
ENV GEANT4_VERSION=11.2.0

# Install dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    libxerces-c-dev \
    libexpat1-dev \
    qtbase5-dev \
    libqt5opengl5-dev \
    libxmu-dev \
    libmotif-dev \
    libssl-dev \
    python3 \
    python3-pip \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Download and build Geant4 (optional - for full functionality)
# This step is commented out to reduce build time
# Uncomment if you need actual Geant4 execution
#
# RUN wget https://gitlab.cern.ch/geant4/geant4/-/archive/v${GEANT4_VERSION}/geant4-v${GEANT4_VERSION}.tar.gz \
#     && tar xzf geant4-v${GEANT4_VERSION}.tar.gz \
#     && mkdir geant4-build && cd geant4-build \
#     && cmake ../geant4-v${GEANT4_VERSION} \
#         -DCMAKE_INSTALL_PREFIX=/opt/geant4 \
#         -DGEANT4_INSTALL_DATA=ON \
#         -DGEANT4_USE_OPENGL_X11=OFF \
#         -DGEANT4_USE_QT=OFF \
#     && make -j$(nproc) \
#     && make install \
#     && cd .. && rm -rf geant4-v${GEANT4_VERSION}* geant4-build

# Stage 2: Python API
FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY run.py .

# Create directories
RUN mkdir -p results logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
ENV GEANT4_USE_SUBPROCESS=true
ENV RESULTS_PATH=/app/results
ENV LOG_LEVEL=INFO

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')" || exit 1

# Run the application
CMD ["python", "run.py"]

