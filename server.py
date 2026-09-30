"""
Production-Ready FastAPI Server for Agno Agent + AgnoCommerce Gaming Transactions
Menyediakan REST API & SSE Real-time Streaming, Rate Limiting, dan Session Management.
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

# Add project root to sys.path
BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR))

from src.agent_factory import create_commerce_agent, run_agent_with_failover, ALL_COMMERCE_TOOLS
from tools.commerce_tools import DATABASE_CATALOG, ORDERS_DB

app = FastAPI(
    title="AgnoCommerce Agentic AI Gateway",
    description="Backend API Gateway untuk AI Agent Transaksi AgnoCommerce berbasis Agno",
    version="2.0.0"
)

# Enable CORS for Next.js / React / Vite frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 1. RATE LIMITING & ANTI-SPAM SYSTEM
# ==========================================
# Melindungi server dari bot spam tanpa mewajibkan user login
RATE_LIMIT_WINDOW_SECONDS = 60
MAX_REQUESTS_PER_MINUTE = 15
ip_request_history = defaultdict(list)

def check_rate_limit(request: Request):
    """Membatasi request maksimal 15 chat / menit per IP."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    
    # Clean old requests
    timestamps = [t for t in ip_request_history[client_ip] if now - t < RATE_LIMIT_WINDOW_SECONDS]
    ip_request_history[client_ip] = timestamps
    
    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=429,
            detail="Terlalu banyak permintaan chat. Mohon tunggu 1 menit sebelum mengirim pesan lagi."
        )
    
    ip_request_history[client_ip].append(now)
    return client_ip


# ==========================================
# 2. SESSION STORE (IN-MEMORY CACHE)
# ==========================================
# Menyimpan instance agent per session_id agar memiliki conversation context
session_agents: Dict[str, Any] = {}

def get_or_create_agent(session_id: str):
    if session_id not in session_agents:
        session_agents[session_id] = create_commerce_agent(session_id=session_id)
    return session_agents[session_id]


# ==========================================
# 3. REQUEST / RESPONSE SCHEMAS
# ==========================================
class ChatRequest(BaseModel):
    message: str = Field(..., description="Pesan dari user", example="Berapa harga 86 diamond ML?")
    session_id: Optional[str] = Field(None, description="UUID sesi anonymous dari browser", example="anon-uuid-12345")
    game_context: Optional[str] = Field(None, description="Game yang sedang dibuka di halaman web")

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
    provider = os.getenv("AI_PROVIDER", "openrouter")
    return {
        "status": "online",
        "service": "AgnoCommerce AI Agno Gateway",
        "provider": provider,
        "tools_count": len(ALL_COMMERCE_TOOLS)
    }


@app.get("/api/catalog")
def get_catalog():
    """Mengambil katalog lengkap produk gaming AgnoCommerce"""
    return {"status": "success", "catalog": DATABASE_CATALOG}


@app.get("/api/orders/{invoice_id}")
def get_order_by_invoice(invoice_id: str):
    """Cek invoice transaksi"""
    inv = invoice_id.upper().strip()
    if inv in ORDERS_DB:
        return {"status": "success", "order": ORDERS_DB[inv]}
    raise HTTPException(status_code=404, detail=f"Invoice {invoice_id} tidak ditemukan.")


@app.post("/api/chat", response_model=ChatResponse, dependencies=[Depends(check_rate_limit)])
def chat_standard(req: ChatRequest):
    """Endpoint chat standar (JSON Request -> JSON Response)."""
    session_id = req.session_id or f"anon-{int(time.time()*1000)}"
    
    try:
        response = run_agent_with_failover(req.message, session_id=session_id)
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
    agent = get_or_create_agent(session_id)
    
    def event_generator():
        try:
            response_stream = agent.run(req.message, stream=True)
            for chunk in response_stream:
                content = chunk.content if hasattr(chunk, "content") else str(chunk)
                if content:
                    yield f"data: {content}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as err:
            yield f"data: [ERROR] {str(err)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ==========================================
# 5. STATIC FILES (SLIDES & CHAT WIDGET)
# ==========================================
# Serve interactive slide presentation
slides_path = BASE_DIR / "slides"
if slides_path.exists():
    app.mount("/slides", StaticFiles(directory=str(slides_path), html=True), name="slides")

# Serve frontend widget
frontend_path = BASE_DIR / "frontend"
if frontend_path.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_path), html=True), name="frontend")

@app.get("/")
def home():
    """Redirect to Presentation Slides or Frontend"""
    return FileResponse(str(BASE_DIR / "frontend" / "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    print(f"🚀 AgnoCommerce Agno Gateway running on http://localhost:{port}")
    print(f"📊 Presentation Deck: http://localhost:{port}/slides")
    print(f"🎮 Live Chat Widget: http://localhost:{port}/frontend")
    print(f"📖 Swagger Docs: http://localhost:{port}/docs")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
