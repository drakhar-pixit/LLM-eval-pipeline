from llm_client import call_judge_llm
from metrics import calculate_metrics
from typing import Dict, List
import re
import httpx
import os


class Evaluator:
    """Main evaluation orchestrator with new scoring strategy"""
    
    def __init__(self):
        print("Initializing Evaluator...")
        self.SLA_MS = 10000
        self.MAX_COST = 0.001
        self.vector_encoder_url = os.getenv('VECTOR_ENCODER_URL', 'http://vector-encoder:8001')
        print("Evaluator initialized")
        
    async def evaluate_turn(
        self,
        turn_number: int,
        user_query: str,
        ai_response: str,
        context_vectors: List[str],
        context_vector_data: List[Dict],
        all_vectors_for_cost: List[Dict],
        timestamp_user: str,
        timestamp_ai: str,
        vector_ids: List[int] = None
    ) -> Dict:
        """Evaluate a single conversation turn"""
        
        print(f"\n{'='*60}")
        print(f"Evaluating Turn {turn_number}")
        print(f"{'='*60}")
        
        # Call LLM Judge
        print(f"Calling Judge LLM with vector IDs: {vector_ids}...")
        llm_judgment = await call_judge_llm(
            user_query=user_query,
            ai_response=ai_response,
            context_vectors=context_vectors,
            vector_ids=vector_ids
        )
        print(f"  LLM Judgment received")
        
        # Calculate metrics (use all vectors for cost calculation)
        print("Calculating metrics...")
        metrics_result = calculate_metrics(
            timestamp_user=timestamp_user,
            timestamp_ai=timestamp_ai,
            context_vectors=all_vectors_for_cost
        )
        
        # Apply new scoring strategy
        scores = await self._calculate_scores(
            user_query, ai_response, llm_judgment, metrics_result, context_vectors
        )
        
        print(f"  Relevance: {scores['relevance']:.2f}")
        print(f"  Completeness: {scores['completeness']:.2f}")
        print(f"  Hallucination: {scores['hallucination']:.2f}")
        print(f"  Latency: {scores['latency']:.2f}")
        print(f"  Cost: {scores['cost']:.2f}")
        print(f"  Overall: {scores['overall']:.2f}")
        
        # Format hallucinated claims for entailment_check
        hallucinated_claims = llm_judgment.get("hallucinated_claims", [])
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
                "confidence": scores['hallucination']
            },
            "llm_judgment": llm_judgment,
            "metrics": metrics_result,
            "scores": scores,
            "used_llm": True
        }
        
        print(f"{'='*60}\n")
        
        return result
    
    async def _calculate_scores(self, query: str, response: str, judgment: Dict, metrics: Dict, context: List[str]) -> Dict:
        """Calculate all scores using new strategy"""
        
        # 2.1 Relevance Score (use LLM judgment)
        R = judgment.get("relevance_score", 0.8)
        
        # 2.2 Completeness Score (less harsh penalty)
        C = judgment.get("completeness_score", 0.5)
        response_len = len(response.split())
        expected_len = max(30, len(query.split()) * 5)
        length_factor = min(1.0, response_len / expected_len)
        C = C * (0.7 + 0.3 * length_factor)
        
        # 3. Hallucination Score
        H = self._calculate_hallucination_score(response, judgment, context)
        
        # 4.1 Latency Score
        latency_ms = metrics.get("latency_ms", 0)
        L = max(0, 1 - (latency_ms / self.SLA_MS))
        
        # 4.2 Cost Score
        cost_usd = metrics.get("cost_usd", 0)
        K = max(0, 1 - (cost_usd / self.MAX_COST))
        
        # Overall Score (weighted: H=40%, C=30%, R=20%, L=5%, K=5%)
        overall = (R * 0.2 + C * 0.3 + H * 0.4 + L * 0.05 + K * 0.05)
        
        return {
            "relevance": R,
            "completeness": C,
            "hallucination": H,
            "latency": L,
            "cost": K,
            "overall": overall
        }
    
    def _calculate_hallucination_score(self, response: str, judgment: Dict, context: List[str]) -> float:
        """Calculate hallucination score with severity weighting"""
        
        hallucinated_claims = judgment.get("hallucinated_claims", [])
        
        if not hallucinated_claims:
            return 1.0
        
        # Extract factual claims (simple heuristic)
        sentences = re.split(r'[.!?]+', response)
        factual_claims = [s.strip() for s in sentences if s.strip() and self._is_factual(s)]
        
        if not factual_claims:
            return 1.0
        
        # Calculate severity-weighted hallucination penalty
        total_severity = 0
        weighted_penalty = 0
        
        for claim in hallucinated_claims:
            claim_text = claim if isinstance(claim, str) else claim.get("claim", "")
            severity = self._get_severity(claim_text)
            confidence = 0.0  # Hallucinated claims have 0 confidence
            
            total_severity += severity
            weighted_penalty += severity * (1 - confidence)
        
        if total_severity == 0:
            return 1.0
        
        H = 1 - (weighted_penalty / total_severity)
        return max(0, min(1, H))
    
    def _is_factual(self, sentence: str) -> bool:
        """Check if sentence contains factual claim"""
        opinion_words = ['think', 'believe', 'feel', 'opinion', 'seems', 'appears']
        return not any(word in sentence.lower() for word in opinion_words)
    
    async def _get_cosine_similarity(self, text1: str, text2: str) -> float:
        """Get cosine similarity from vector encoder service"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.vector_encoder_url}/similarity",
                    json={"text1": text1, "text2": text2}
                )
                if response.status_code == 200:
                    return response.json().get("similarity", 0.5)
        except:
            pass
        return 0.5
    
    def _get_severity(self, claim: str) -> float:
        """Determine severity of hallucinated claim"""
        claim_lower = claim.lower()
        
        # Medical/Safety: 1.0
        if any(word in claim_lower for word in ['medical', 'health', 'safety', 'risk', 'treatment', 'diagnosis']):
            return 1.0
        
        # Financial/Legal: 0.7
        if any(word in claim_lower for word in ['cost', 'price', 'rs', '$', 'payment', 'legal', 'contract']):
            return 0.7
        
        # Logistics/Metadata: 0.3
        if any(word in claim_lower for word in ['room', 'hotel', 'location', 'time', 'schedule']):
            return 0.3
        
        # Default
        return 0.5
    
    def calculate_overall_score(self, evaluations: List[Dict]) -> float:
        """Calculate overall score from all evaluations"""
        if not evaluations:
            return 0.0
        
        total_score = sum(e.get("scores", {}).get("overall", 0) for e in evaluations)
        return round((total_score / len(evaluations)) * 100, 2)
