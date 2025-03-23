#!/bin/bash

# Create necessary directories
mkdir -p uploads

# Check if Docker is installed
if ! [ -x "$(command -v docker)" ]; then
  echo 'Error: Docker is not installed.' >&2
  echo 'Please install Docker before proceeding: https://docs.docker.com/get-docker/' >&2
  exit 1
fi

# Check if Docker Compose is installed
if ! [ -x "$(command -v docker-compose)" ]; then
  echo 'Error: Docker Compose is not installed.' >&2
  echo 'Please install Docker Compose before proceeding: https://docs.docker.com/compose/install/' >&2
  exit 1
fi

# Build Docker image
echo "Building Docker image..."
docker-compose build

# Start services
echo "Starting application..."
docker-compose up -d