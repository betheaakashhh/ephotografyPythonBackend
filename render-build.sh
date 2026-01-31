#!/bin/bash
echo "🚀 Starting build process..."

# Install system dependencies for OpenCV and other packages
apt-get update
apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-glx \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages with pip
echo "📦 Installing Python packages..."
pip install --no-cache-dir -r requirements.txt

# Create necessary directories
mkdir -p uploads/jobs
echo "✅ Build completed!"