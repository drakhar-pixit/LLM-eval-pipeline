import os

# Judge LLM Configuration
JUDGE_LLM_URL = os.getenv("JUDGE_LLM_URL", "http://judge-llm:11434")

# Cross-Encoder Configuration
CROSS_ENCODER_MODEL = os.getenv(
    "CROSS_ENCODER_MODEL", 
    "cross-encoder/nli-deberta-v3-small"  # Proper NLI model
)

# Thresholds
ENTAILMENT_THRESHOLD = float(os.getenv("ENTAILMENT_THRESHOLD", "0.5"))
CONTRADICTION_THRESHOLD = float(os.getenv("CONTRADICTION_THRESHOLD", "0.3"))

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3:mini")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))
