# Speed Optimization Guide

## Current Performance
- 6 turns × 9 seconds = **54 seconds total**
- Sequential processing (one turn at a time)

## Optimization 1: Parallel Turn Evaluation (6x faster)

### Change in main.py:

```python
# BEFORE (Sequential - SLOW)
evaluations = []
for i, ai_turn in enumerate(ai_turns):
    eval_result = await evaluator.evaluate_turn(...)
    evaluations.append(eval_result)

# AFTER (Parallel - FAST)
import asyncio

tasks = []
for i, ai_turn in enumerate(ai_turns):
    task = evaluator.evaluate_turn(...)
    tasks.append(task)

evaluations = await asyncio.gather(*tasks)
```

**Result:** 54s → 9s (6x faster)

---

## Optimization 2: Batch LLM Calls

Instead of calling Ollama once per turn, batch multiple prompts:

```python
# Send 6 prompts at once to Ollama
responses = await ollama_batch_call(prompts=[...])
```

**Result:** Additional 2-3x speedup

---

## Optimization 3: Use Faster Model

Current: `phi3:mini` (3.8B params)
Alternative: `gemma2:2b` (2B params - 2x faster)

```bash
docker exec judge-llm ollama pull gemma2:2b
```

Update docker-compose.yml:
```yaml
OLLAMA_MODEL=gemma2:2b
```

**Result:** 9s → 4-5s per turn

---

## Optimization 4: GPU Acceleration

If you have GPU:
```yaml
judge-llm:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

**Result:** 5-10x faster inference

---

## Combined Optimizations

| Optimization | Time | Speedup |
|--------------|------|---------|
| Current (Sequential) | 54s | 1x |
| + Parallel Processing | 9s | 6x |
| + Faster Model | 4.5s | 12x |
| + GPU | 1-2s | 27-54x |

---

## Quick Win: Implement Parallel Processing

**File:** `/Users/prdixit2501/Documents/LLM-eval/services/evaluation-service/main.py`

**Line 88-110:** Replace the for loop with asyncio.gather()

```python
# Create all tasks
tasks = []
for i, ai_turn in enumerate(ai_turns):
    user_turn = None
    for turn in request.conversation.conversation_turns:
        if turn.turn == ai_turn.turn - 1 and turn.role == "User":
            user_turn = turn
            break
    
    if user_turn is None:
        continue
    
    task = evaluator.evaluate_turn(
        turn_number=ai_turn.turn,
        user_query=user_turn.message,
        ai_response=ai_turn.message,
        context_vectors=context_texts,
        context_vector_data=vector_data,
        timestamp_user=user_turn.created_at,
        timestamp_ai=ai_turn.created_at
    )
    tasks.append(task)

# Execute all in parallel
evaluations = await asyncio.gather(*tasks)
```

**Rebuild:** `docker-compose build evaluation-service && docker-compose up -d`

**Test:** Your 54s request will now take ~9s
