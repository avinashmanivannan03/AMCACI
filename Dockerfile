# AMCACI 
# Multi-stage Docker build for production deployment

# Stage 1: Base image with system dependencies

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # FFmpeg for audio/video processing
    ffmpeg \
    # Build tools for Python packages
    build-essential \
    gcc \
    g++ \
    # Git for model downloads
    git \
    # Audio processing libraries
    libsndfile1 \
    libsox-fmt-all \
    # Video processing libraries
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    # System utilities
    curl \
    wget \
    unzip \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Verify FFmpeg installation
RUN ffmpeg -version


# Stage 2: Python dependencies installation

FROM base as dependencies

# Create application directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel

# Install PyTorch with CPU support (smaller image, can be changed for GPU)
RUN pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cpu

# Install other dependencies
RUN pip install -r requirements.txt

# Pre-download critical models to reduce startup time
RUN python -c "import whisper; whisper.load_model('medium')" || echo "Whisper model download failed, will retry at runtime"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || echo "SBERT model download failed, will retry at runtime"
RUN python -c "from transformers import pipeline; pipeline('zero-shot-classification', model='facebook/bart-large-mnli')" || echo "BART model download failed, will retry at runtime"
RUN python -c "from transformers import pipeline; pipeline('summarization', model='facebook/bart-large-cnn')" || echo "BART CNN model download failed, will retry at runtime"


# Stage 3: Application setup

FROM dependencies as application

# Create non-root user for security
RUN groupadd -r amcaci && useradd -r -g amcaci -s /bin/bash amcaci

# Create necessary directories
RUN mkdir -p /app/data/temp \
             /app/data/outputs \
             /app/data/logs \
             /app/models \
    && chown -R amcaci:amcaci /app

# Copy application code
COPY --chown=amcaci:amcaci . /app/

# Set working directory
WORKDIR /app

# Switch to non-root user
USER amcaci

# Create .env file from example if it doesn't exist
RUN if [ ! -f .env ]; then cp .env.example .env; fi


# Stage 4: Production image

FROM application as production

# Expose ports
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Default command - run Streamlit web interface
CMD ["streamlit", "run", "streamlit_page.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]


# Stage 5: Development image 

FROM application as development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN pip install \
    pytest \
    black \
    mypy \
    flake8 \
    jupyter \
    ipython

# Install additional debugging tools
RUN apt-get update && apt-get install -y \
    vim \
    htop \
    tree \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Switch back to amcaci user
USER amcaci

# Development command - keep container running
CMD ["tail", "-f", "/dev/null"]


# Stage 6: GPU-enabled image 

FROM nvidia/cuda:11.8-runtime-ubuntu22.04 as gpu-base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    ffmpeg \
    build-essential \
    gcc \
    g++ \
    git \
    libsndfile1 \
    libsox-fmt-all \
    libavcodec-extra \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    curl \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python
RUN ln -s /usr/bin/python3.11 /usr/bin/python && \
    ln -s /usr/bin/python3.11 /usr/bin/python3

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .

# Install PyTorch with CUDA support
RUN pip install torch==2.2.0 torchaudio==2.2.0 --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
RUN pip install -r requirements.txt

# Create user and directories
RUN groupadd -r amcaci && useradd -r -g amcaci -s /bin/bash amcaci
RUN mkdir -p /app/data/temp /app/data/outputs /app/data/logs /app/models && \
    chown -R amcaci:amcaci /app

# Copy application
COPY --chown=amcaci:amcaci . /app/

USER amcaci

# Pre-download models for GPU
RUN python -c "import whisper; whisper.load_model('medium')" || echo "Whisper model download failed"
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')" || echo "SBERT model download failed"

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_page.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true", "--server.enableCORS=false", "--server.enableXsrfProtection=false"]