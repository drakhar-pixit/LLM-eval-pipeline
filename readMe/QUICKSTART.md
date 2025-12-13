# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Start Services
```bash
cd /Users/prdixit2501/Documents/LLM-eval
docker-compose up -d --build
```

This will:
- Build evaluation-service image (~2 minutes)
- Build judge-llm image (~1 minute)
- Start both containers

### Step 2: Download Model (One-time)
```bash
./scripts/setup-ollama.sh
```

This downloads Phi-3 Mini (~2.3GB). Takes 2-5 minutes depending on internet speed.

**The model is stored in a Docker volume and persists across restarts!**

### Step 3: Test Evaluation
```bash
./scripts/test-api.sh
```

This will:
- Send sample conversation + context to the API
- Display evaluation results
- Show hallucination detection

### Step 4: View Detailed Logs
```bash
docker logs -f evaluation-service
```

You'll see:
- Cross-encoder analysis
- LLM judge calls (when needed)
- Detailed evaluation results
- Formatted output

## 📊 Expected Output

```
═══════════════════════════════════════════════════════════
🔍 LLM EVALUATION RESULTS
═══════════════════════════════════════════════════════════

📝 Conversation ID: 78128
👤 User ID: 77096
🔄 Total Turns: 18
🤖 AI Responses Evaluated: 9

📊 Overall Score: 62/100 ⚠️

───────────────────────────────────────────────────────────
📈 SUMMARY
───────────────────────────────────────────────────────────
Hallucinations Detected: 1
LLM Calls Made: 3
Cross-Encoder Only: 6
Avg Relevance: 0.85
Avg Completeness: 0.78
Total Cost: $0.0023
Avg Latency: 234ms

───────────────────────────────────────────────────────────
🚨 TURN 14 - CRITICAL ISSUE
───────────────────────────────────────────────────────────

User Query:
"Do you have an idea how much their rooms cost per night?"

AI Response:
"For Gopal Mansion, an air-conditioned room with TV and bath 
is Rs 800 per night. We also offer specially subsidized 
air-conditioned rooms at our clinic for Rs 2000..."

❌ Hallucination Detected
Confidence: 94%

Hallucinated Claims:
  • "We offer subsidized rooms at our clinic for Rs 2000"

═══════════════════════════════════════════════════════════
✅ Evaluation Complete
═══════════════════════════════════════════════════════════
```

## 🔧 Common Commands

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# Evaluation service
docker logs -f evaluation-service

# Judge LLM
docker logs -f judge-llm

# Both
docker-compose logs -f
```

### Restart Services
```bash
docker-compose restart
```

### Stop Services
```bash
docker-compose down
```

### Clean Everything
```bash
./scripts/cleanup.sh
```

## 🧪 Test with Your Own Data

1. Create your request JSON:
```bash
cat > my-request.json <<EOF
{
  "conversation": {
    "chat_id": 12345,
    "user_id": 67890,
    "conversation_turns": [
      {
        "turn": 1,
        "sender_id": 67890,
        "role": "User",
        "message": "What is your pricing?",
        "created_at": "2024-01-15T10:00:00.000000Z"
      },
      {
        "turn": 2,
        "sender_id": 1,
        "role": "AI/Chatbot",
        "message": "Our pricing starts at $99/month.",
        "created_at": "2024-01-15T10:00:01.000000Z"
      }
    ]
  },
  "context_vectors": {
    "status": "success",
    "status_code": 200,
    "message": "Success",
    "data": {
      "vector_data": [
        {
          "id": 1,
          "text": "Pricing: Basic plan is $49/month, Pro plan is $99/month",
          "tokens": 15,
          "created_at": "2024-01-01T00:00:00.000Z"
        }
      ]
    }
  }
}
EOF
```

2. Send request:
```bash
curl -X POST http://localhost:8000/api/evaluate \
  -H "Content-Type: application/json" \
  -d @my-request.json | jq '.'
```

## 🐛 Troubleshooting

### "Connection refused" error
```bash
# Wait for services to be ready
docker-compose ps

# Check health
curl http://localhost:8000/health
curl http://localhost:11434/api/tags
```

### "Model not found" error
```bash
# Re-download model
docker exec judge-llm ollama pull phi3:mini

# Verify
docker exec judge-llm ollama list
```

### Slow responses
```bash
# Check if model is loaded
docker exec judge-llm ollama list

# Check resource usage
docker stats
```

### Out of memory
```bash
# Use smaller model
docker exec judge-llm ollama pull gemma2:2b

# Update docker-compose.yml:
# OLLAMA_MODEL=gemma2:2b

# Restart
docker-compose restart
```

## 📚 Next Steps

- Read [README.md](README.md) for detailed architecture
- Explore API at http://localhost:8000/docs
- Customize thresholds in docker-compose.yml
- Try different models (gemma2:2b, qwen2.5:3b)

## 🎯 Key Features

✅ **Cross-Encoder Pre-filtering** - Filters 60% of cases locally  
✅ **LLM Judge** - Detailed analysis when needed  
✅ **Hallucination Detection** - Catches fabricated claims  
✅ **Cost Optimization** - Reduces LLM calls by 60%  
✅ **Volume Persistence** - Download model once, use forever  
✅ **Small Model** - Phi-3 Mini (3.8B) runs on CPU  

Enjoy! 🚀
