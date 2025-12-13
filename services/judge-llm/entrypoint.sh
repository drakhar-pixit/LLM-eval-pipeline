#!/bin/bash
set -e

echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

echo "Waiting for Ollama to start..."
sleep 10

echo "Ollama server started with PID: $OLLAMA_PID"
echo "Ready to serve requests on port 11434"

wait $OLLAMA_PID
