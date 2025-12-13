from datetime import datetime
from dateutil import parser
from typing import List, Dict


def calculate_metrics(
    timestamp_user: str,
    timestamp_ai: str,
    context_vectors: List[Dict]
) -> Dict:
    """
    Calculate latency and cost metrics
    """
    
    # Calculate latency
    try:
        time_user = parser.parse(timestamp_user)
        time_ai = parser.parse(timestamp_ai)
        latency_ms = (time_ai - time_user).total_seconds() * 1000
    except Exception as e:
        print(f"Error calculating latency: {e}")
        latency_ms = 0.0
    
    # Calculate tokens used
    tokens_used = sum(vec.get("tokens", 0) for vec in context_vectors)
    
    # Estimate cost (example: $0.0001 per 1000 tokens)
    cost_per_1k_tokens = 0.0001
    cost_usd = (tokens_used / 1000) * cost_per_1k_tokens
    
    return {
        "latency_ms": round(latency_ms, 2),
        "cost_usd": round(cost_usd, 6),
        "tokens_used": tokens_used
    }
