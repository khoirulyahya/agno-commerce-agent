"""
FastAPI Server Gateway untuk Libra Books AI Assistant
Menyediakan REST API & Server-Sent Events (SSE) streaming untuk integrasi Frontend Web.
Dilengkapi rate limiting dan multi-provider key failover.
"""
import os
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Optional, Dict, Any, List

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

from src.agent_factory import create_commerce_agent, run_agent_with_failover, ALL_COMMERCE_TOOLS
from tools.commerce_tools import DATABASE_CATALOG, ORDERS_DB

app = FastAPI(
    title="Libra Books AI Gateway",
    description="Production-grade AI Gateway using Agno, FastAPI, and multi-provider failover for digital bookstore transactions.",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files (Frontend Web & Slides)
app.mount("/slides", StaticFiles(directory=str(BASE_DIR / "slides"), html=True), name="slides")
app.mount("/frontend", StaticFiles(directory=str(BASE_DIR / "frontend"), html=True), name="frontend")
app.mount("/screenshots", StaticFiles(directory=str(BASE_DIR / "screenshots")), name="screenshots")


# ==========================================
# 1. SIMPLE IN-MEMORY RATE LIMITER
# ==========================================
RATE_LIMIT_PER_MINUTE = 15
request_history = defaultdict(list)

def check_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    request_history[client_ip] = [t for t in request_history[client_ip] if now - t < 60]
    
    if len(request_history[client_ip]) >= RATE_LIMIT_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Maximum 15 requests per minute."
        )
    
    request_history[client_ip].append(now)
    return True


# ==========================================
# 2. SESSION & AGENT REGISTRY
# ==========================================
session_agents: Dict[str, Any] = {}

def get_or_create_agent(session_id: str, language: str = "en"):
    key = f"{session_id}_{language}"
    if key not in session_agents:
        session_agents[key] = create_commerce_agent(session_id=session_id, language=language)
    return session_agents[key]


# ==========================================
# 3. REQUEST / RESPONSE SCHEMAS
# ==========================================
class ChatRequest(BaseModel):
    message: str = Field(..., description="Message from user")
    session_id: Optional[str] = Field(None, description="Anonymous session UUID from browser")
    language: Optional[str] = Field("en", description="Language code: 'en' or 'id'")

class ChatResponse(BaseModel):
    success: bool
    session_id: str
    reply: str
    timestamp: float


# ==========================================
# 4. API ROUTES
# ==========================================
@app.get("/api/health")
def health_check():
    provider = os.getenv("AI_PROVIDER", "gemini")
    return {
        "status": "online",
        "service": "Libra Books AI Gateway",
        "provider": provider,
        "tools_count": len(ALL_COMMERCE_TOOLS)
    }


@app.get("/api/catalog")
def get_catalog():
    """Mengembalikan katalog buku digital."""
    return {"status": "success", "catalog": DATABASE_CATALOG}


@app.get("/api/orders/{invoice_id}")
def get_order_status(invoice_id: str):
    """Mengecek status order / invoice pembelian buku."""
    inv = invoice_id.upper().strip()
    if inv in ORDERS_DB:
        return {"status": "success", "order": ORDERS_DB[inv]}
    raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} not found.")


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(check_rate_limit)])
def chat_standard(req: ChatRequest):
    """Endpoint chat standar (JSON Request -> JSON Response)."""
    session_id = req.session_id or f"anon-{int(time.time()*1000)}"
    lang = req.language or "en"
    
    try:
        response = run_agent_with_failover(req.message, session_id=session_id, language=lang)
        reply_content = response.content if hasattr(response, "content") else str(response)
        
        return ChatResponse(
            success=True,
            session_id=session_id,
            reply=reply_content,
            timestamp=time.time()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Agent Error: {str(e)}")


@app.post("/api/chat/stream", dependencies=[Depends(check_rate_limit)])
async def chat_stream(req: ChatRequest):
    """Endpoint real-time SSE streaming (efek ketik live per kata)."""
    session_id = req.session_id or f"anon-{int(time.time()*1000)}"
    lang = req.language or "en"
    agent = get_or_create_agent(session_id, language=lang)
    
    def event_generator():
        try:
            response_stream = agent.run(req.message, stream=True)
            for chunk in response_stream:
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    clean_content = content.replace("\n", "\\n")
                    yield f"data: {clean_content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# Root / -> serve chatbot UI
@app.get("/")
def serve_root():
    return FileResponse(str(BASE_DIR / "frontend" / "index.html"))


if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🚀 Libra Books AI Gateway running on http://localhost:8000")
    print("📊 Presentation Deck: http://localhost:8000/slides")
    print("📚 Live Chat Widget: http://localhost:8000/")
    print("📖 Swagger Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run("server.py:app", host="0.0.0.0", port=8000, reload=True)
