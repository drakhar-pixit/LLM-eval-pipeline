from sentence_transformers import CrossEncoder
from typing import List, Tuple, Dict
import numpy as np
import re
import config


class EntailmentChecker:
    """
    Cross-encoder for Natural Language Inference (NLI)
    Detects if AI response is entailed/contradicted by context
    """
    
    def __init__(self, model_name: str = None):
        if model_name is None:
            model_name = config.CROSS_ENCODER_MODEL
        
        print(f"Loading cross-encoder model: {model_name}")
        self.model = CrossEncoder(model_name)
        print("Cross-encoder model loaded successfully")
        
    def check_entailment(self, context: str, claim: str) -> Tuple[float, str]:
        """
        Check if claim is entailed by context
        
        Returns:
            (score, label)
            score: 0-1 (higher = more entailed)
            label: "entailment" | "neutral" | "contradiction"
        """
        # Cross-encoder takes pairs: (premise, hypothesis)
        score = self.model.predict([(context, claim)])[0]
        
        # Convert to 0-1 scale (sigmoid)
        score = float(1 / (1 + np.exp(-score)))
        
        # Classify
        if score > config.ENTAILMENT_THRESHOLD:
            label = "entailment"
        elif score < config.CONTRADICTION_THRESHOLD:
            label = "contradiction"
        else:
            label = "neutral"
            
        return score, label
    
    def check_hallucination(
        self,
        context_vectors: List[str],
        ai_response: str
    ) -> Dict:
        """
        Check if AI response contains hallucinations
        
        Strategy:
        1. Split AI response into sentences
        2. For each sentence, check against all context vectors
        3. If ANY context entails it → OK
        4. If ALL contexts contradict/neutral → Hallucination
        """
        # Split response into sentences
        sentences = self._split_sentences(ai_response)
        
        if not sentences:
            return {
                "hallucination_detected": False,
                "hallucinated_claims": [],
                "all_sentences": [],
                "confidence": 1.0
            }
        
        results = []
        hallucinated_claims = []
        
        for sentence in sentences:
            max_score = 0
            best_label = "neutral"
            
            # Check against all context vectors
            for context in context_vectors:
                score, label = self.check_entailment(context, sentence)
                if score > max_score:
                    max_score = score
                    best_label = label
            
            # If no context supports this claim
            if best_label in ["contradiction", "neutral"] and max_score < 0.5:
                hallucinated_claims.append({
                    "claim": sentence,
                    "score": max_score,
                    "label": best_label
                })
            
            results.append({
                "sentence": sentence,
                "entailment_score": max_score,
                "label": best_label
            })
        
        # Calculate confidence: average of max scores across all sentences
        avg_confidence = sum(r["entailment_score"] for r in results) / len(results) if results else 0.0
        
        return {
            "hallucination_detected": len(hallucinated_claims) > 0,
            "hallucinated_claims": hallucinated_claims,
            "all_sentences": results,
            "confidence": avg_confidence
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Simple sentence splitter"""
        # Remove URLs and markdown links
        text = re.sub(r'\[.*?\]\(.*?\)', '', text)
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Split by sentence terminators
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]
