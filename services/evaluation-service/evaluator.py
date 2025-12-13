from llm_client import call_judge_llm
from metrics import calculate_metrics
from typing import Dict, List


class Evaluator:
    """Main evaluation orchestrator"""
    
    def __init__(self):
        print("Initializing Evaluator...")
        print("Evaluator initialized (no pre-filtering)")
        
    async def evaluate_turn(
        self,
        turn_number: int,
        user_query: str,
        ai_response: str,
        context_vectors: List[str],
        context_vector_data: List[Dict],
        timestamp_user: str,
        timestamp_ai: str,
        vector_ids: List[int] = None
    ) -> Dict:
        """Evaluate a single conversation turn"""
        
        print(f"\n{'='*60}")
        print(f"Evaluating Turn {turn_number}")
        print(f"{'='*60}")
        
        # Call LLM Judge directly (no pre-filtering)
        print(f"Calling Judge LLM with vector IDs: {vector_ids}...")
        llm_judgment = await call_judge_llm(
            user_query=user_query,
            ai_response=ai_response,
            context_vectors=context_vectors,
            vector_ids=vector_ids
        )
        print(f"  LLM Judgment received")
        
        # Calculate metrics
        print("Calculating metrics...")
        metrics_result = calculate_metrics(
            timestamp_user=timestamp_user,
            timestamp_ai=timestamp_ai,
            context_vectors=context_vector_data
        )
        
        print(f"  Latency: {metrics_result['latency_ms']}ms")
        print(f"  Cost: ${metrics_result['cost_usd']}")
        print(f"  Tokens: {metrics_result['tokens_used']}")
        
        # Ensure required fields are present
        if "hallucinated_claims" not in llm_judgment:
            llm_judgment["hallucinated_claims"] = []
        
        # Combine results
        hallucinated_claims = llm_judgment.get("hallucinated_claims", [])
        # Convert strings to dict format if needed
        formatted_claims = []
        for claim in hallucinated_claims:
            if isinstance(claim, str):
                formatted_claims.append({"claim": claim, "score": 0.0, "label": "hallucination"})
            else:
                formatted_claims.append(claim)
        
        result = {
            "turn": turn_number,
            "user_query": user_query,
            "ai_response": ai_response,
            "entailment_check": {
                "hallucination_detected": llm_judgment.get("hallucination", False),
                "hallucinated_claims": formatted_claims,
                "all_sentences": [],
                "confidence": 0.0 if llm_judgment.get("hallucination") else 1.0
            },
            "llm_judgment": llm_judgment,
            "metrics": metrics_result,
            "used_llm": True
        }
        
        print(f"{'='*60}\n")
        
        return result
    
    def calculate_overall_score(self, evaluations: List[Dict]) -> float:
        """Calculate overall score from all evaluations"""
        if not evaluations:
            return 0.0
        
        total_score = 0
        for eval_result in evaluations:
            # Penalize hallucinations heavily
            hallucination_penalty = 0
            if eval_result["llm_judgment"]["hallucination"]:
                hallucination_penalty = 40
            
            # Score based on relevance and completeness
            relevance = eval_result["llm_judgment"].get("relevance_score", 0.5) * 30
            completeness = eval_result["llm_judgment"].get("completeness_score", 0.5) * 30
            
            turn_score = max(0, relevance + completeness - hallucination_penalty)
            total_score += turn_score
        
        return round(total_score / len(evaluations), 2)
