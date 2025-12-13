@echo off
echo Setting up LLM Evaluation Pipeline...
echo.

REM Check if GPU is available
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo NVIDIA GPU detected
    set COMPOSE_FILE=docker-compose.gpu.yml
    echo Using GPU-accelerated setup
) else (
    echo No GPU detected
    set COMPOSE_FILE=docker-compose.yml
    echo Using CPU-only setup
)

echo.
echo Starting Docker containers...
docker-compose -f %COMPOSE_FILE% up -d

echo.
echo Waiting for services to start...
timeout /t 10 /nobreak >nul

echo.
echo Pulling Ollama model (qwen2.5:7b)...
docker exec judge-llm ollama pull qwen2.5:7b

echo.
echo Setup complete!
echo.
echo Test the pipeline:
echo    curl -X POST http://localhost:8000/api/evaluate ^
echo      -H "Content-Type: application/json" ^
echo      -d @test_payload.json
echo.
echo View logs:
echo    docker-compose -f %COMPOSE_FILE% logs -f
