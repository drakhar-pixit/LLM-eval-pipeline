FROM --platform=linux/amd64 ollama/ollama:latest

# Set GPU environment variables
ENV OLLAMA_GPU_LAYERS=99
ENV OLLAMA_NUM_PARALLEL=4
ENV OLLAMA_MAX_LOADED_MODELS=1

EXPOSE 11434

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:11434/api/tags || exit 1

ENTRYPOINT ["/entrypoint.sh"]
