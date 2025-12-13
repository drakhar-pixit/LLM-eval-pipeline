#!/bin/bash
set -e

ollama serve &
OLLAMA_PID=$!

sleep 5

if ! ollama list | grep -q "phi3:mini"; then
    echo "Downloading phi3:mini model..."
    ollama pull phi3:mini
fi

wait $OLLAMA_PID
