# LLM Evaluation Pipeline

An automated evaluation system for testing AI chatbot responses against hallucination, relevance, and completeness using cross-encoder pre-filtering and LLM-as-judge.

## Architecture

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose                            │
│                                                               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Pod 1: Evaluation Service (Port 8000)             │    │
│  │  • FastAPI REST API                                │    │
│  │  • Cross-Encoder (ms-marco-MiniLM-L-6-v2)         │    │
│  │  • Entailment checking (local)                     │    │
│  │  • Metrics calculation                             │    │
│  │  • Result aggregation                              │    │
│  └────────────────┬───────────────────────────────────┘    │
│                   │                                          │
│                   │ HTTP calls (only when needed)           │
│                   │                                          │
│  ┌────────────────▼───────────────────────────────────┐    │
│  │  Pod 2: Judge LLM Service (Port 11434)            │    │
│  │  • Ollama server                                   │    │
│  │  • Phi-3 Mini (3.8B parameters)                    │    │
│  │  • Volume: ollama-models (persistent)             │    │
│  └────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

### Evaluation Flow

1. **Input**: Conversation JSON + Context Vectors JSON
2. **Cross-Encoder Pre-Filter** (Local, Fast):
   - Compute entailment scores for each sentence
   - Score > 0.7: Entailed (PASS, skip LLM)
   - Score < 0.3: Contradiction (potential hallucination)
   - Score 0.3-0.7: Neutral (needs LLM verification)
3. **Judge LLM** (Only when needed, ~40% of cases):
   - Detailed hallucination analysis
   - Relevance scoring
   - Completeness checking
4. **Metrics Calculation**:
   - Latency (timestamp diff)
   - Cost (token count)
5. **Output**: Structured JSON + Formatted terminal output

## Why This Architecture?

### Cross-Encoder vs Cosine Similarity

**Problem with Cosine Similarity:**
```
Context: "Gopal Mansion costs Rs 800 per night"
AI Claim: "Our clinic offers rooms for Rs 2000 per night"

Cosine Similarity: 0.85 ✅ (HIGH - both talk about rooms & prices)
Reality: HALLUCINATION ❌ (clinic doesn't offer rooms)
```

**Solution with Cross-Encoder:**
```
Cross-Encoder (NLI):
- Entailment: Context supports the claim
- Contradiction: Context contradicts the claim
- Neutral: Context doesn't mention it

Result: CONTRADICTION ❌ (Hallucination detected!)
```

### Small Language Model (SLM) Choice

**Phi-3 Mini (3.8B parameters)**
- Size: ~2.3GB
- Speed: Fast inference on CPU
- Quality: Good reasoning for evaluation tasks
- Cost: Free (runs locally)
- Alternative: Can swap with `gemma2:2b`, `qwen2.5:3b`, `llama3.2:3b`

### Volume Strategy

**Why not bake models into images?**
- ❌ Image size: 2-10GB (unpushable to registries)
- ❌ Slow builds
- ❌ Wasted bandwidth

**Volume approach:**
- ✅ Download once, persist forever
- ✅ Small Docker images (~500MB)
- ✅ Fast container restarts
- ✅ Easy model swapping

## Project Structure

```
llm-eval-microservices/
├── services/
│   ├── evaluation-service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── main.py              # FastAPI app
│   │   ├── models.py            # Pydantic models
│   │   ├── config.py            # Configuration
│   │   ├── evaluator.py         # Main orchestrator
│   │   ├── cross_encoder.py     # Entailment checker
│   │   ├── llm_client.py        # Ollama client
│   │   └── metrics.py           # Metrics calculation
│   │
│   └── judge-llm/
│       └── Dockerfile           # Ollama server
│
├── data/
│   ├── sample-chat-conversation-01.json
│   └── sample_context_vectors-01.json
│
├── scripts/
│   ├── setup-ollama.sh          # Download model
│   ├── test-api.sh              # Test evaluation
│   └── cleanup.sh               # Cleanup resources
│
├── docker-compose.yml
└── README.md
```

## Setup Instructions

### Prerequisites

- Docker & Docker Compose
- 8GB RAM minimum
- 10GB disk space (for model weights)

### Quick Start

1. **Clone/Navigate to project:**
```bash
cd /Users/prdixit2501/Documents/LLM-eval
```

2. **Build and start services:**
```bash
docker-compose up -d --build
```

3. **Download Phi-3 Mini model** (one-time, ~2.3GB):
```bash
./scripts/setup-ollama.sh
```

4. **Test the evaluation:**
```bash
./scripts/test-api.sh
```

5. **View logs:**
```bash
docker logs -f evaluation-service
```

### Manual Testing

```bash
# Build request
cat > request.json <<EOF
{
  "conversation": $(cat data/sample-chat-conversation-01.json),
  "context_vectors": $(cat data/sample_context_vectors-01.json)
}
EOF

# Send request
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d @request.json | jq '.'
```

## Evaluation Parameters

### 1. Hallucination Detection

**Method:** Cross-Encoder + LLM Judge

**Metrics:**
- Entailment score (0-1)
- Hallucinated claims (list)
- Confidence (0-1)

**Example Output:**
```
🚨 TURN 14 - CRITICAL ISSUE
❌ Hallucination Detected
Confidence: 94%

Hallucinated Claims:
  • "We offer subsidized rooms at our clinic for Rs 2000"
  • "Non-AC rooms for Rs 1500 per night"
```

### 2. Relevance & Completeness

**Method:** LLM Judge (when needed)

**Metrics:**
- Relevance score (0-1): Does it answer the question?
- Completeness score (0-1): Covers all key info?
- Missing info (list)

### 3. Latency & Cost

**Method:** Direct calculation (no LLM)

**Metrics:**
- Latency: Timestamp difference (ms)
- Cost: Token count × price per token
- Tokens used: Sum from context vectors

## Scalability for Millions of Conversations

### Current Optimizations

1. **Cross-Encoder Pre-Filtering**
   - Filters ~60% of cases locally
   - Reduces LLM calls by 60%
   - Cost savings: ~$0.60 per 1000 evaluations

2. **Async Processing**
   - Non-blocking I/O
   - Parallel evaluation of turns

3. **Volume Persistence**
   - Model loaded once
   - Fast container restarts

### Future Enhancements

1. **Caching Layer**
   - Redis for LLM response caching
   - Cache similar queries
   - Additional 30% cost reduction

2. **Batch Processing**
   - Process multiple conversations in parallel
   - Queue-based architecture (RabbitMQ/Kafka)

3. **Horizontal Scaling**
   - Multiple evaluation service replicas
   - Load balancer (Nginx)
   - Single Judge LLM serves all replicas

4. **Model Optimization**
   - Quantization (4-bit/8-bit)
   - Smaller models for simple cases
   - GPU acceleration for high throughput

### Estimated Performance at Scale

**For 1 million conversations/day:**

| Metric | Without Optimization | With Cross-Encoder | With Caching |
|--------|---------------------|-------------------|--------------|
| LLM Calls | 1M | 400K | 280K |
| Avg Time | 1000ms | 400ms | 200ms |
| Daily Cost | $1000 | $400 | $280 |
| Throughput | 1K/s | 2.5K/s | 5K/s |

## Configuration

### Environment Variables

```bash
# Judge LLM
JUDGE_LLM_URL=http://judge-llm:11434
OLLAMA_MODEL=phi3:mini
OLLAMA_TIMEOUT=60

# Cross-Encoder
CROSS_ENCODER_MODEL=cross-encoder/ms-marco-MiniLM-L-6-v2
ENTAILMENT_THRESHOLD=0.7
CONTRADICTION_THRESHOLD=0.3
```

### Swap Models

**Change Judge LLM:**
```bash
# In docker-compose.yml, update:
OLLAMA_MODEL=gemma2:2b  # or qwen2.5:3b, llama3.2:3b

# Then:
docker-compose restart judge-llm
./scripts/setup-ollama.sh
```

**Change Cross-Encoder:**
```bash
# In docker-compose.yml, update:
CROSS_ENCODER_MODEL=cross-encoder/nli-deberta-v3-base  # More accurate, slower

docker-compose restart evaluation-service
```

## API Documentation

### POST /api/evaluate

**Request:**
```json
{
  "conversation": {
    "chat_id": 78128,
    "user_id": 77096,
    "conversation_turns": [...]
  },
  "context_vectors": {
    "status": "success",
    "data": {
      "vector_data": [...]
    }
  }
}
```

**Response:**
```json
{
  "conversation_id": 78128,
  "user_id": 77096,
  "total_turns": 18,
  "ai_responses_evaluated": 9,
  "overall_score": 62.5,
  "evaluations": [...],
  "summary": {
    "hallucinations_detected": 1,
    "llm_calls_made": 3,
    "cross_encoder_only": 6,
    "avg_relevance": 0.85,
    "avg_completeness": 0.78,
    "total_cost": 0.0023,
    "avg_latency_ms": 234
  }
}
```

### GET /health

Health check endpoint.

### GET /ready

Readiness check endpoint.

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Restart
docker-compose restart
```

### Model not found
```bash
# Re-download model
./scripts/setup-ollama.sh

# Or manually:
docker exec judge-llm ollama pull phi3:mini
```

### Out of memory
```bash
# Use smaller model
OLLAMA_MODEL=gemma2:2b ./scripts/setup-ollama.sh

# Or increase Docker memory limit
# Docker Desktop → Settings → Resources → Memory: 8GB
```

### Slow evaluation
```bash
# Check if using GPU (if available)
docker exec judge-llm nvidia-smi

# Reduce timeout
OLLAMA_TIMEOUT=30 docker-compose up
```

## Cleanup

```bash
# Stop services
docker-compose down

# Remove everything (including models)
./scripts/cleanup.sh
```

## Technologies Used

- **FastAPI**: REST API framework
- **Ollama**: LLM inference engine
- **Phi-3 Mini**: Small language model (3.8B)
- **sentence-transformers**: Cross-encoder models
- **Docker Compose**: Container orchestration
- **Pydantic**: Data validation

## License

MIT

## Author

Priyanshu Dixit
BeyondChats LLM Engineer Internship Assignment
