import httpx
from typing import List, Dict, Any, Optional

class VectorClient:
    def __init__(self, base_url: str = "http://vector-encoder:8001"):
        self.base_url = base_url
    
    async def select_most_relevant_vector(self, user_query: str, vectors: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Call the vector encoder service to select the most relevant vector"""
        if not vectors:
            return None
        
        if len(vectors) == 1:
            return vectors[0]
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/select-vector",
                    json={
                        "user_query": user_query,
                        "vectors": vectors
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("selected_vector")
            except Exception as e:
                print(f"Error calling vector encoder service: {e}")
                # Fallback to first vector if service fails
                return vectors[0] if vectors else None