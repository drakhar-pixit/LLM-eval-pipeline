from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import json

app = FastAPI()

conversations = {}
current_conversation_id = None

@app.get("/")
async def read_root():
    return FileResponse("index.html")

@app.post("/api/results")
async def receive_results(data: dict):
    global conversations, current_conversation_id
    conv_id = data.get('conversation_id')
    conversations[conv_id] = data
    current_conversation_id = conv_id
    return {"status": "success"}

@app.get("/api/results")
async def get_results():
    if current_conversation_id and current_conversation_id in conversations:
        return conversations[current_conversation_id]
    return {}

@app.get("/api/conversations")
async def get_conversations():
    return {"conversations": list(conversations.keys())}

@app.get("/api/results/{conv_id}")
async def get_conversation(conv_id: int):
    global current_conversation_id
    current_conversation_id = conv_id
    return conversations.get(conv_id, {})

@app.websocket("/ws/logs")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            conv_list = [{"id": k, "score": v.get("overall_score", 0)} for k, v in conversations.items()]
            await websocket.send_text(json.dumps({"conversations": conv_list, "current": current_conversation_id}))
            await asyncio.sleep(1)
    except:
        pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
