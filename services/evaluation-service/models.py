from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class ConversationTurn(BaseModel):
    turn: int
    sender_id: int
    role: str
    message: str
    created_at: str


class ConversationInput(BaseModel):
    chat_id: int
    user_id: int
    conversation_turns: List[ConversationTurn]


class VectorData(BaseModel):
    id: int
    source_url: Optional[str] = None
    text: str
    tokens: int
    created_at: str


class ContextVectorsInput(BaseModel):
    status: str
    status_code: int
    message: str
    data: Dict[str, Any]


class EvaluationRequest(BaseModel):
    conversation: ConversationInput
    context_vectors: ContextVectorsInput


class EntailmentResult(BaseModel):
    sentence: str
    entailment_score: float
    label: str  # "entailment" | "neutral" | "contradiction"


class HallucinationCheck(BaseModel):
    hallucination_detected: bool
    hallucinated_claims: List[Dict[str, Any]]
    all_sentences: List[EntailmentResult]
    confidence: float


class LLMJudgment(BaseModel):
    hallucination: bool
    hallucinated_claims: List[str]
    relevance_score: float
    completeness_score: float
    missing_info: List[str]
    method: str


class Metrics(BaseModel):
    latency_ms: float
    cost_usd: float
    tokens_used: int


class TurnEvaluation(BaseModel):
    turn: int
    user_query: str
    ai_response: str
    entailment_check: HallucinationCheck
    llm_judgment: LLMJudgment
    metrics: Metrics
    used_llm: bool


class EvaluationResult(BaseModel):
    conversation_id: int
    user_id: int
    total_turns: int
    ai_responses_evaluated: int
    evaluations: List[TurnEvaluation]
    overall_score: float
    summary: Dict[str, Any]
