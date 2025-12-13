import httpx
import json
from typing import Dict, List
import config


async def call_judge_llm(
    user_query: str,
    ai_response: str,
    context_vectors: List[str],
) -> Dict:
    """
    Call Ollama Judge LLM for detailed evaluation
    """
    
    # Merge all context vectors into single paragraph
    context_str = " ".join(context_vectors)
    
    # Build prompt with clear structure
    prompt = f"""USER QUERY:
{user_query}

CONTEXT:
{context_str}

AI RESPONSE:
{ai_response}

QUESTION: Is there any information stated in the AI response that is NOT present in the context above? If yes, mark it as a hallucination.

Return JSON:
{{"hallucination": true/false, "hallucinated_claims": ["specific information not in context"], "relevance_score": 0.0-1.0, "completeness_score": 0.0-1.0, "missing_info": []}}
"""

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
                
                # Normalize hallucinated_claims to list of strings
                if "hallucinated_claims" in judgment:
                    claims = judgment["hallucinated_claims"]
                    if isinstance(claims, list):
                        judgment["hallucinated_claims"] = [
                            str(c) if not isinstance(c, str) else c 
                            for c in claims
                        ]
                
                # Normalize missing_info to list of strings
                if "missing_info" in judgment:
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
