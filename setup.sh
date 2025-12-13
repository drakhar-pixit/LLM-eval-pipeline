#!/bin/bash

echo "Setting up LLM Evaluation Pipeline..."
echo ""

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "NVIDIA GPU detected"
    COMPOSE_FILE="docker-compose.gpu.yml"
    echo "Using GPU-accelerated setup"
else
    echo "No GPU detected"
    COMPOSE_FILE="docker-compose.yml"
    echo "Using CPU-only setup"
fi

echo ""
echo "Starting Docker containers..."
docker-compose -f $COMPOSE_FILE up -d

echo ""
echo "Waiting for services to start..."
sleep 10

echo ""
echo "Pulling Ollama model (qwen2.5:7b)..."
docker exec judge-llm ollama pull qwen2.5:7b

echo ""
echo "Setup complete!"
echo ""
echo "Test the pipeline:"
echo "   curl -X POST http://localhost:8000/api/evaluate \\"
echo "     -H 'Content-Type: application/json' \\"
echo "     -d @test_payload.json"
echo ""
echo "View logs:"
echo "   docker-compose -f $COMPOSE_FILE logs -f"
