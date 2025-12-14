import httpx
import json
from typing import Dict, List
import config


async def call_judge_llm(
    user_query: str,
    ai_response: str,
    context_vectors: List[str],
    vector_ids: List[int] = None,
) -> Dict:
    """
    Call Ollama Judge LLM for detailed evaluation
    """
    
    # Merge all context vectors into single paragraph
    context_str = " ".join(context_vectors)
    vector_ids_str = str(vector_ids) if vector_ids else "[unknown]"
    
    # Build prompt with clear structure and vector IDs for debugging
    prompt = f"""USER QUERY:
{user_query}

CONTEXT (Vector IDs: {vector_ids_str}):
{context_str}

AI RESPONSE:
{ai_response}

QUESTION: Is there any information stated in the AI response that is NOT present in the context above? If yes, mark it as a hallucination.

Return JSON:
{{"hallucination": true/false, "hallucinated_claims": ["specific information not in context"], "relevance_score": 0.0-1.0, "completeness_score": 0.0-1.0, "missing_info": [], "context_vector_ids_used": {vector_ids_str}}}
"""
    
    # Debug logging
    if "legal" in ai_response.lower() or "subsidized" in ai_response.lower():
        print(f"\n{'='*80}")
        print(f"DEBUG: AI response contains 'legal' or 'subsidized'")
        print(f"Vector IDs: {vector_ids_str}")
        print(f"Context length: {len(context_str)} chars")
        print(f"Context contains 'legal': {'legal' in context_str.lower()}")
        print(f"Context contains 'contract': {'contract' in context_str.lower()}")
        print(f"Context contains 'subsidized': {'subsidized' in context_str.lower()}")
        print(f"{'='*80}\n")

    try:
        timeout = httpx.Timeout(7200.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{config.JUDGE_LLM_URL}/api/generate",
                json={
                    "model": config.OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {
                        "num_predict": 150,
                        "temperature": 0.1,
                        "num_ctx": 4096,
                        "num_thread": 8,
                        "num_batch": 512,
                        "top_k": 10,
                        "top_p": 0.9,
                        "repeat_penalty": 1.1
                    }
                }
            )
            response.raise_for_status()
            
            result = response.json()
            llm_output = result.get("response", "{}")
            
            # Parse JSON response
            try:
                judgment = json.loads(llm_output)
                
                # Ensure required fields exist
                if "hallucinated_claims" not in judgment:
                    judgment["hallucinated_claims"] = []
                if "missing_info" not in judgment:
                    judgment["missing_info"] = []
                
                # Normalize hallucinated_claims to list of strings
                claims = judgment["hallucinated_claims"]
                if isinstance(claims, list):
                    judgment["hallucinated_claims"] = [
                        str(c) if not isinstance(c, str) else c 
                        for c in claims
                    ]
                
                # Normalize missing_info to list of strings
                info = judgment["missing_info"]
                if isinstance(info, list):
                    judgment["missing_info"] = [
                        str(i) if not isinstance(i, str) else i 
                        for i in info
                    ]
                        
            except json.JSONDecodeError:
                # Fallback if LLM doesn't return valid JSON
                judgment = {
                    "hallucination": False,
                    "hallucinated_claims": [],
                    "relevance_score": 0.5,
                    "completeness_score": 0.5,
                    "missing_info": []
                }
            
            judgment["method"] = "llm_judge"
            
            # Debug logging for legal contracts and subsidized rooms
            if "legal" in ai_response.lower() or "subsidized" in ai_response.lower():
                print(f"\nDEBUG LLM Response:")
                print(f"  Hallucination detected: {judgment.get('hallucination')}")
                print(f"  Claims: {judgment.get('hallucinated_claims')}\n")
            
            return judgment
            
    except Exception as e:
        print(f"Error calling Judge LLM: {e}")
        # Return safe default
        return {
            "hallucination": False,
            "hallucinated_claims": [],
            "relevance_score": 0.5,
            "completeness_score": 0.5,
            "missing_info": [],
            "method": "llm_judge_error",
            "error": str(e)
        }
