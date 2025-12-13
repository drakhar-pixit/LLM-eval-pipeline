#!/bin/bash

echo "Setting up GPU-accelerated LLM Evaluation Pipeline..."

# Check if NVIDIA Docker runtime is available
if ! docker info | grep -q nvidia; then
    echo "Warning: NVIDIA Docker runtime not detected. GPU acceleration may not work."
    echo "Please install nvidia-docker2 package and restart Docker daemon."
    echo ""
    echo "Installation commands:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install -y nvidia-docker2"
    echo "  sudo systemctl restart docker"
    echo ""
fi

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "GPU Status:"
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
    echo ""
else
    echo "Warning: nvidia-smi not found. GPU may not be available."
    echo ""
fi

# Build and start GPU-enabled services
echo "Building and starting GPU-enabled services..."
docker-compose -f docker-compose.gpu.yml up -d --build

echo "Waiting for services to start..."
sleep 10

# Download Qwen model with GPU optimization
echo "Downloading Qwen 2.5:7B model..."
docker exec judge-llm-gpu ollama pull qwen2.5:7b

echo ""
echo "GPU setup complete!"
echo "Services running:"
echo "  - Judge LLM (GPU): http://localhost:11434"
echo "  - Evaluation API: http://localhost:8000"
echo ""
echo "Test GPU usage with:"
echo "  docker exec judge-llm-gpu nvidia-smi"