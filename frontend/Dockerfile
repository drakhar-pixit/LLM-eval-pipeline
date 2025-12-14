FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn websockets

COPY server.py .
COPY index.html .

EXPOSE 3000

CMD ["python", "server.py"]
