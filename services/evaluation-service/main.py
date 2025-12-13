from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models import EvaluationRequest, EvaluationResult, ConversationInput, ContextVectorsInput
from evaluator import Evaluator
from typing import Dict, List
import json
import re

app = FastAPI(title="LLM Evaluation Service", version="1.0.0")

# Initialize evaluator at startup
evaluator = None

@app.on_event("startup")
async def startup_event():
    global evaluator
    print("Starting Evaluation Service...")
    evaluator = Evaluator()
    print("Evaluation Service ready!")




@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/ready")
async def ready():
    """Readiness check endpoint"""
    if evaluator is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {"status": "ready"}


def clean_json_string(text: str) -> str:
    """Remove comments and trailing commas from JSON string"""
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
    text = re.sub(r',\s*([}\]])', r'\1', text)
    text = ''.join(c if ord(c) >= 32 or c in '\n\t\r' else ' ' for c in text)
    return text

@app.post("/api/evaluate-raw")
async def evaluate_raw(request: Request):
    """Endpoint that accepts and cleans malformed JSON"""
    body = await request.body()
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        cleaned = clean_json_string(body.decode('utf-8'))
        data = json.loads(cleaned)
    
    eval_request = EvaluationRequest(**data)
    return await evaluate(eval_request)

@app.post("/api/evaluate", response_model=EvaluationResult)
async def evaluate(conversation: ConversationInput, context_vectors: ContextVectorsInput):
    """
    Main evaluation endpoint
    Accepts conversation and context vectors as separate payloads
    """
    request = EvaluationRequest(conversation=conversation, context_vectors=context_vectors)
    
    print("\n" + "="*80)
    print("NEW EVALUATION REQUEST")
    print("="*80)
    print(f"Conversation ID: {request.conversation.chat_id}")
    print(f"User ID: {request.conversation.user_id}")
    print(f"Total Turns: {len(request.conversation.conversation_turns)}")
    
    try:
        # Extract context - use only vectors_used
        vector_data = request.context_vectors.data.get("vector_data", [])
        vectors_used_ids = request.context_vectors.data.get("sources", {}).get("vectors_used", [])
        
        if vectors_used_ids:
            # Filter to only the vectors actually used by RAG
            vector_id_map = {vec.get("id"): vec for vec in vector_data}
            used_vectors = [vector_id_map[vid] for vid in vectors_used_ids if vid in vector_id_map]
            context_texts = [vec.get("text", "") for vec in used_vectors if vec.get("text")]
            print(f"Context: Using {len(context_texts)} vectors from vectors_used (filtered from {len(vector_data)} total)")
        else:
            # Fallback to all vectors
            context_texts = [vec.get("text", "") for vec in vector_data if vec.get("text")]
            print(f"Context Vectors: {len(context_texts)} (all vectors)")
        
        # Extract AI responses from conversation
        ai_turns = [
            turn for turn in request.conversation.conversation_turns 
            if turn.role == "AI/Chatbot"
        ]
        
        print(f"AI Responses to Evaluate: {len(ai_turns)}")
        
        # Evaluate each AI response in batches
        import asyncio
        
        # Prepare all evaluation tasks
        tasks = []
        for ai_turn in ai_turns:
            # Find corresponding user query (previous turn)
            user_turn = None
            for turn in request.conversation.conversation_turns:
                if turn.turn == ai_turn.turn - 1 and turn.role == "User":
                    user_turn = turn
                    break
            
            if user_turn is None:
                print(f"Warning: No user query found for turn {ai_turn.turn}")
                continue
            
            # Create task
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
        
        # Process in batches of 10
        BATCH_SIZE = 10
        evaluations = []
        for i in range(0, len(tasks), BATCH_SIZE):
            batch = tasks[i:i + BATCH_SIZE]
            print(f"Processing batch {i//BATCH_SIZE + 1} ({len(batch)} turns)...")
            batch_results = await asyncio.gather(*batch)
            evaluations.extend(batch_results)
        
        # Calculate overall score
        overall_score = evaluator.calculate_overall_score(evaluations)
        
        # Generate summary
        hallucinations = sum(1 for e in evaluations if e["llm_judgment"]["hallucination"])
        llm_calls = sum(1 for e in evaluations if e["used_llm"])
        
        summary = {
            "total_evaluations": len(evaluations),
            "hallucinations_detected": hallucinations,
            "llm_calls_made": llm_calls,
            "cross_encoder_only": len(evaluations) - llm_calls,
            "avg_relevance": round(
                sum(e["llm_judgment"]["relevance_score"] for e in evaluations) / len(evaluations), 2
            ) if evaluations else 0,
            "avg_completeness": round(
                sum(e["llm_judgment"]["completeness_score"] for e in evaluations) / len(evaluations), 2
            ) if evaluations else 0,
            "total_cost": round(
                sum(e["metrics"]["cost_usd"] for e in evaluations), 6
            ),
            "avg_latency_ms": round(
                sum(e["metrics"]["latency_ms"] for e in evaluations) / len(evaluations), 2
            ) if evaluations else 0
        }
        
        # Convert dicts to TurnEvaluation objects
        from models import TurnEvaluation, HallucinationCheck, LLMJudgment, Metrics
        
        eval_objects = []
        for e in evaluations:
            eval_obj = TurnEvaluation(
                turn=e["turn"],
                user_query=e["user_query"],
                ai_response=e["ai_response"],
                entailment_check=HallucinationCheck(**e["entailment_check"]),
                llm_judgment=LLMJudgment(**e["llm_judgment"]),
                metrics=Metrics(**e["metrics"]),
                used_llm=e["used_llm"]
            )
            eval_objects.append(eval_obj)
        
        # Build result
        result = EvaluationResult(
            conversation_id=request.conversation.chat_id,
            user_id=request.conversation.user_id,
            total_turns=len(request.conversation.conversation_turns),
            ai_responses_evaluated=len(evaluations),
            evaluations=eval_objects,
            overall_score=overall_score,
            summary=summary
        )
        
        # Print formatted results
        print_results(result)
        
        return result
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


def print_results(result: EvaluationResult):
    """Print formatted evaluation results to stdout"""
    
    print("\n" + "="*80)
    print("LLM EVALUATION RESULTS")
    print("="*80)
    print(f"\nConversation ID: {result.conversation_id}")
    print(f"User ID: {result.user_id}")
    print(f"Total Turns: {result.total_turns}")
    print(f"AI Responses Evaluated: {result.ai_responses_evaluated}")
    print(f"\nOverall Score: {result.overall_score}/100")
    
    print("\n" + "-"*80)
    print("SUMMARY")
    print("-"*80)
    print(f"Hallucinations Detected: {result.summary['hallucinations_detected']}")
    print(f"LLM Calls Made: {result.summary['llm_calls_made']}")
    print(f"Avg Relevance: {result.summary['avg_relevance']}")
    print(f"Avg Completeness: {result.summary['avg_completeness']}")
    print(f"Total Cost: ${result.summary['total_cost']}")
    print(f"Avg Latency: {result.summary['avg_latency_ms']}ms")
    
    # Print detailed findings
    for eval_result in result.evaluations:
        print("\n" + "-"*80)
        print(f"TURN {eval_result.turn}")
        print("-"*80)
        print(f"\nUser Query:\n{eval_result.user_query}")
        ai_resp = eval_result.ai_response
        print(f"\nAI Response:\n{ai_resp[:200]}..." if len(ai_resp) > 200 else f"\nAI Response:\n{ai_resp}")
        
        if eval_result.llm_judgment.hallucination:
            print(f"\nHallucination: YES")
            if eval_result.llm_judgment.hallucinated_claims:
                print("\nHallucinated Information:")
                for claim in eval_result.llm_judgment.hallucinated_claims:
                    print(f"  • {claim}")
        else:
            print(f"\nHallucination: NO")
    
    print("\n" + "="*80)
    print("Evaluation Complete")
    print("="*80 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
