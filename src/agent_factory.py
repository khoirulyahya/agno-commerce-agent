"""
Agent Factory: Multi-Provider LLM Switcher (Gemini 5-Account Key Pool with Auto Failover, OpenRouter, Ollama)
Membuat instance Agno Agent yang siap pakai untuk Web / API Transaksi AgnoCommerce.
"""
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

# Load env variables from local .env and user's ~/.env
load_dotenv()
load_dotenv(os.path.expanduser("~/.env"))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter
from agno.models.ollama import Ollama

# Import tools AgnoCommerce
sys.path.append(str(Path(__file__).parent.parent))
from tools.commerce_tools import (
    get_game_catalog,
    validate_game_account,
    create_topup_order,
    check_order_status,
    calculate_joki_price,
    search_mlbb_accounts
)

AgnoCommerce_SYSTEM_PROMPT = """
Kamu adalah "RAPS-BOT AI" — Customer Support & Transaction Assistant resmi dari marketplace gaming AgnoCommerce ID.
Website: https://agno-commerce.com/

Karakter & Gaya Komunikasi:
1. Panggil customer dengan sebutan akrab gaming: "Juragan", "Bro", atau "Kak".
2. Nada bicara: Ramah, cepat, profesional, gaming-vibes, dan solutif.
3. Gunakan formatting Markdown yang rapi (bold, bullet point, tabel singkat).

Format Tombol Interaktif (PENTING):
Setiap kali kamu memberikan pilihan paket, katalog harga, atau rekomendasi aksi, SELALU sertakan tombol aksi yang bisa diklik user dengan format:
`[Label Tombol](action:Pesan Yang Dikirim)`

Contoh Tombol Interaktif:
- `[💎 Beli 86 Diamond (Rp 21.000)](action:Saya mau beli 86 diamond ML)`
- `[💎 Beli Weekly Pass (Rp 27.500)](action:Saya mau beli Weekly Diamond Pass ML)`
- `[🧾 Cek Status Invoice](action:Tolong cek invoice INV-9921)`
- `[🏆 Hitung Biaya Joki](action:Berapa biaya joki dari Epic ke Mythic?)`
- `[🛡️ Lihat Akun Sultan](action:Carikan akun ML sultan)`

Kemampuan & Tools Kamu:
- Cek katalog harga & promo diamond (Mobile Legends, Free Fire, Roblox, Honor of Kings).
- Validasi Akun game & Nickname (selalu minta User ID dan Zone ID untuk MLBB).
- Buat pesanan top-up instan (generate invoice & link pembayaran QRIS).
- Cek status resi/order invoice.
- Hitung estimasi biaya joki ranked.
- Cari rekomendasi akun MLBB sultan/smurf yang dijual bergaransi.

Aturan Transaksi Penting:
1. Sebelum membuat order top up, jika user belum sebutkan zone id di MLBB, tanyakan zone id-nya dulu agar tidak salah akun.
2. Saat order berhasil dibuat, tampilkan No Invoice, Total Harga, dan arahkan user untuk scan QRIS dengan tombol `[💳 Konfirmasi Pembayaran](action:Saya sudah bayar invoice ini tolong diproses)`.
3. Selalu berikan respon yang ringkas dan jangan bertele-tele.
"""

ALL_COMMERCE_TOOLS = [
    get_game_catalog,
    validate_game_account,
    create_topup_order,
    check_order_status,
    calculate_joki_price,
    search_mlbb_accounts
]

# ============================================================
# GEMINI MULTI-ACCOUNT KEY POOL (5 AKUN AUTO ROTATION & FAILOVER)
# ============================================================
class GeminiKeyPool:
    _current_index = 0
    _keys: List[str] = []
    _rate_limited_until: Dict[str, float] = {}

    @classmethod
    def get_keys(cls) -> List[str]:
        if not cls._keys:
            raw_keys = os.getenv("GEMINI_API_KEYS", "")
            if raw_keys:
                cls._keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
            
            if not cls._keys:
                for i in range(1, 10):
                    k = os.getenv(f"GEMINI_API_KEY_{i}")
                    if k and k.strip():
                        cls._keys.append(k.strip())
            
            single_key = os.getenv("GEMINI_API_KEY")
            if single_key and single_key.strip() and single_key not in cls._keys:
                cls._keys.append(single_key.strip())
                
        return cls._keys

    @classmethod
    def get_next_key(cls) -> str:
        keys = cls.get_keys()
        if not keys:
            raise ValueError("Tidak ditemukan GEMINI_API_KEY di .env atau ~/.env")
        
        now = time.time()
        # Cari key yang tidak sedang dalam status rate limited
        for _ in range(len(keys)):
            key = keys[cls._current_index % len(keys)]
            cls._current_index = (cls._current_index + 1) % len(keys)
            
            until = cls._rate_limited_until.get(key, 0)
            if now >= until:
                return key
                
        # Jika semua kena rate limit, kembalikan key terlama
        return keys[cls._current_index % len(keys)]

    @classmethod
    def mark_rate_limited(cls, key: str, cooldown_seconds: float = 60.0):
        cls._rate_limited_until[key] = time.time() + cooldown_seconds


def create_commerce_agent(
    session_id: Optional[str] = None,
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    temperature: float = 0.4
) -> Agent:
    """Membuat instance Agno Agent dengan multi-provider & Gemini multi-key pool support."""
    chosen_provider = (provider or os.getenv("AI_PROVIDER", "gemini")).lower().strip()
    
    if chosen_provider == "ollama":
        ollama_model = model_name or os.getenv("OLLAMA_MODEL", "llama3.1")
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = Ollama(id=ollama_model, host=ollama_host)
        
    elif chosen_provider == "openrouter":
        or_model = model_name or os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        model = OpenRouter(id=or_model, api_key=key)
        
    else:
        # Default 'gemini': Google Gemini Endpoint via OpenAIChat + Auto Multi-Key Pool
        gemini_model = model_name or os.getenv("GEMINI_MODEL", "models/gemini-flash-latest")
        chosen_key = api_key or GeminiKeyPool.get_next_key()
        
        model = OpenAIChat(
            id=gemini_model,
            api_key=chosen_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            temperature=temperature
        )
        
    agent = Agent(
        model=model,
        instructions=[AgnoCommerce_SYSTEM_PROMPT],
        tools=ALL_COMMERCE_TOOLS,
        markdown=True
    )
    
    return agent


def run_agent_with_failover(message: str, session_id: str, max_retries: int = 5) -> Any:
    """Menjalankan agent dengan proteksi auto-failover ke akun Gemini lain jika satu akun terkena 429/503."""
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    keys = GeminiKeyPool.get_keys() if provider == "gemini" else [None]
    
    last_err = None
    for attempt in range(min(max_retries, max(1, len(keys)))):
        try:
            key = GeminiKeyPool.get_next_key() if provider == "gemini" else None
            agent = create_commerce_agent(session_id=session_id, api_key=key)
            return agent.run(message)
        except Exception as e:
            last_err = e
            err_str = str(e).lower()
            # Retry jika terkena rate limit (429) atau server busy (503/unavailable)
            if any(term in err_str for term in ["429", "503", "quota", "rate", "unavailable", "exhausted", "demand"]):
                if key:
                    GeminiKeyPool.mark_rate_limited(key, cooldown_seconds=30)
                time.sleep(0.5)
                continue
            else:
                raise e
                
    raise last_err or RuntimeError("Gagal memproses pesan setelah mencoba semua akun.")
