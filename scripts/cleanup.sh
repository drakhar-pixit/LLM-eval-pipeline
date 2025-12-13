#!/bin/bash

echo "Cleaning up LLM Evaluation Pipeline..."

# Stop and remove containers
docker-compose down

# Optional: Remove volumes (model weights)
read -p "Do you want to remove model volumes? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose down -v
    echo "Volumes removed"
else
    echo "Volumes preserved (models will persist)"
fi

# Optional: Remove images
read -p "Do you want to remove Docker images? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker rmi llm-eval-evaluation-service llm-eval-judge-llm 2>/dev/null || true
    echo "Images removed"
fi

echo "Cleanup complete!"
