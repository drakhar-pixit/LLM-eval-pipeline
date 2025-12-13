import os

# Judge LLM Configuration
JUDGE_LLM_URL = os.getenv("JUDGE_LLM_URL", "http://judge-llm:11434")

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "7200"))
