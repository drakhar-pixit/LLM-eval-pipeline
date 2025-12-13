#!/bin/bash

set -e

echo "Testing LLM Evaluation API..."

# Check if data files exist
CONV_FILE="data/sample-chat-conversation-01.json"
CTX_FILE="data/sample_context_vectors-01.json"

if [ ! -f "$CONV_FILE" ]; then
    echo "Error: $CONV_FILE not found"
    exit 1
fi

if [ ! -f "$CTX_FILE" ]; then
    echo "Error: $CTX_FILE not found"
    exit 1
fi

# Build request JSON
echo "Building request payload..."
jq -s '{conversation: .[0], context_vectors: .[1]}' "$CONV_FILE" "$CTX_FILE" > /tmp/eval-request.json

# Send request
echo "Sending evaluation request..."
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d @/tmp/eval-request.json \
  | jq '.'

echo ""
echo "Test complete!"
echo ""
echo "View detailed logs:"
echo "  docker logs -f evaluation-service"
