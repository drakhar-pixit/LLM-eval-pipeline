#!/bin/bash

set -e

echo " Setting up Ollama with Phi-3 Mini model..."

# Wait for Ollama to be ready
echo "Waiting for Ollama service to start..."
sleep 10

# Pull the model
echo "Pulling phi3:mini model (this may take a few minutes)..."
docker exec judge-llm ollama pull phi3:mini

echo "Phi-3 Mini model downloaded successfully!"
echo ""
echo "Model info:"
docker exec judge-llm ollama list

echo ""
echo " Setup complete! You can now use the evaluation service."
