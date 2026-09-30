"""
Agent Factory: Multi-Provider LLM Switcher (Gemini 5-Account Key Pool with Auto Failover, OpenRouter, Ollama)
Creates a ready-to-use Agno Agent instance for LibraBot — Digital Bookstore AI Assistant.
"""
import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.expanduser("~/.env"))

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.models.openrouter import OpenRouter
from agno.models.ollama import Ollama

sys.path.append(str(Path(__file__).parent.parent))
from tools.commerce_tools import (
    get_book_catalog,
    get_book_recommendation,
    create_book_order,
    check_order_status,
    get_promo_books
)

ALL_COMMERCE_TOOLS = [
    get_book_catalog,
    get_book_recommendation,
    create_book_order,
    check_order_status,
    get_promo_books
]

def get_system_prompt(language: str = "en") -> str:
    if language == "id":
        return """
Kamu adalah "LibraBot" — AI Asisten resmi dari Libra Books, toko buku digital terpercaya.
Website: https://libra-books.com/

Karakter & Gaya Komunikasi:
1. Panggil pengguna dengan hangat: "Kak", "Sobat Buku", atau pembaca.
2. Nada bicara: Ramah, antusias soal buku, informatif, dan membantu.
3. Gunakan formatting Markdown yang rapi (tabel harga, bullet point, teks tebal).
4. WAJIB menjawab secara menyeluruh dalam Bahasa Indonesia.

Format Tombol Aksi Interaktif (SANGAT PENTING):
Setiap kali kamu merekomendasikan buku atau memberi pilihan aksi, SELALU sertakan tombol aksi interaktif dengan format berikut:
`[Label Tombol](action:Pesan Yang Dikirim)`

Contoh Tombol Interaktif:
- `[📖 Beli Clean Code (Rp 125.000)](action:Saya mau beli buku Clean Code)`
- `[🔥 Lihat Promo Hari Ini](action:Tampilkan semua buku yang sedang promo)`
- `[🧾 Cek Status Pesanan](action:Cek status pesanan invoice INV-0001)`
- `[💡 Rekomendasi Buku Python](action:Rekomendasikan buku untuk belajar Python)`

Kemampuan & Tools:
- Cek katalog buku digital (Programming, Bisnis, Pengembangan Diri, AI/ML).
- Rekomendasi buku berdasarkan minat dan budget.
- Cek buku promo dan diskon.
- Buat pesanan pembelian dan terbitkan invoice + tautan download.
- Cek status resi/invoice pesanan.
"""
    else:
        return """
You are "LibraBot" — the official AI Assistant of Libra Books, a trusted digital bookstore.
Website: https://libra-books.com/

Character & Communication Style:
1. Address the reader warmly (e.g. "Bookworm", "Reader", or by name).
2. Tone: Friendly, enthusiastic about books, informative, and helpful.
3. Use neat Markdown formatting (bold, bullet points, clean price tables).
4. MUST respond entirely in English.

Interactive Action Button Format (VERY IMPORTANT):
Whenever you recommend a book or provide actionable options, ALWAYS include interactive action buttons using this exact format:
`[Button Label](action:Message To Send)`

Example Interactive Buttons:
- `[📖 Buy Clean Code (Rp 125.000)](action:I want to buy the Clean Code book)`
- `[🔥 View Today's Promos](action:Show all books on promo)`
- `[🧾 Check Order Status](action:Check status of order INV-0001)`
- `[💡 Python Recommendations](action:Recommend books to learn Python with a budget under 100k)`

Capabilities & Tools:
- Search digital book catalog across categories (Programming, Business, Self Development, AI/ML).
- Recommend books tailored to user interests and budget.
- Show active promos and discounts.
- Create orders, issue invoices, and generate instant download links.
- Check invoice and download status.
"""

class GeminiKeyPool:
    _current_index = 0
    _keys: List[str] = []

    @classmethod
    def get_keys(cls) -> List[str]:
        if not cls._keys:
            raw_keys = os.getenv("GEMINI_API_KEYS", "")
            if raw_keys:
                cls._keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
            else:
                single_key = os.getenv("GEMINI_API_KEY")
                if single_key:
                    cls._keys = [single_key]
        return cls._keys

    @classmethod
    def get_next_key(cls) -> str:
        keys = cls.get_keys()
        if not keys:
            return ""
        key = keys[cls._current_index]
        cls._current_index = (cls._current_index + 1) % len(keys)
        return key

def create_commerce_agent(
    session_id: Optional[str] = None,
    provider: str = "gemini",
    api_key: Optional[str] = None,
    tools=ALL_COMMERCE_TOOLS,
    language: str = "en"
) -> Agent:
    provider = provider.lower()
    system_prompt = get_system_prompt(language)

    if provider == "gemini":
        chosen_key = api_key or GeminiKeyPool.get_next_key()
        model = OpenAIChat(
            id="gemini-3.5-flash-lite",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=chosen_key
        )
    elif provider == "openrouter":
        model_id = os.getenv("OPENROUTER_MODEL", "google/gemini-2.5-flash")
        model = OpenRouter(id=model_id, api_key=api_key or os.getenv("OPENROUTER_API_KEY"))
    elif provider == "ollama":
        model_id = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
        model = Ollama(id=model_id)
    else:
        raise ValueError(f"Unsupported provider: {provider}")

    return Agent(
        model=model,
        session_id=session_id,
        tools=tools,
        instructions=[system_prompt],
        markdown=True
    )

def run_agent_with_failover(message: str, session_id: str, max_retries: int = 5, language: str = "en") -> Any:
    provider = os.getenv("AI_PROVIDER", "gemini").lower()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            key = GeminiKeyPool.get_next_key() if provider == "gemini" else None
            agent = create_commerce_agent(session_id=session_id, provider=provider, api_key=key, language=language)
            return agent.run(message, stream=False)
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if "429" in error_str or "503" in error_str or "quota" in error_str or "exhausted" in error_str:
                time.sleep(1)
                continue
            else:
                raise e
                
    fallback_provider = "openrouter" if provider == "gemini" else "gemini"
    try:
        agent = create_commerce_agent(session_id=session_id, provider=fallback_provider, language=language)
        return agent.run(message, stream=False)
    except Exception as fallback_e:
        raise Exception(f"All providers failed. Primary error: {last_error}. Fallback error: {fallback_e}")
