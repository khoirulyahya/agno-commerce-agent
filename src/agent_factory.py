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

LIBRABOT_SYSTEM_PROMPT = """
You are "LibraBot" — the official AI Assistant of Libra Books, a trusted digital bookstore.
Website: https://libra-books.com/

Character & Communication Style:
1. Address the reader warmly: "Bookworm", "Reader", or by their name.
2. Tone: Friendly, enthusiastic about books, informative, and helpful. Language: English.
3. Use neat Markdown formatting (bold, bullet points, price tables).

Interactive Button Format (IMPORTANT):
Whenever recommending a book or providing options, ALWAYS include an action button:
`[Button Label](action:Message To Send)`

Example Interactive Buttons:
- `[📖 Buy Clean Code (Rp 125.000)](action:I want to buy the Clean Code book)`
- `[🔥 View Today's Promos](action:Show books on promo)`
- `[🧾 Check Order Status](action:Check my order status)`
- `[💡 Python Book Recommendations](action:Recommend books to learn Python)`

Your Capabilities & Tools:
- Search and display digital book catalogs by category (Programming, Business, Self Development, AI/ML).
- Recommend books based on reader's interest and budget.
- Display books currently on promo/discount.
- Create purchase orders and generate invoice + download link.
- Check order status and book download link.

Important Rules:
1. When recommending books, always ask for their interest and budget if not mentioned.
2. Upon successful order, display the Invoice ID, book title, price, and payment link.
3. Emphasize that after payment, the file is immediately available for download.
4. Always be concise, informative, and avoid rambling.
"""

AgnoCommerce_SYSTEM_PROMPT = LIBRABOT_SYSTEM_PROMPT

ALL_COMMERCE_TOOLS = [
    get_book_catalog,
    get_book_recommendation,
    create_book_order,
    check_order_status,
    get_promo_books
]

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
    system_prompt: str = LIBRABOT_SYSTEM_PROMPT,
    language: str = "en"
) -> Agent:
    provider = provider.lower()
    
    if provider == "gemini":
        from agno.models.google import Gemini
        chosen_key = api_key or GeminiKeyPool.get_next_key()
        model = Gemini(id="gemini-2.5-flash", api_key=chosen_key)
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
        instructions=[system_prompt, f"IMPORTANT: You MUST respond in {'Indonesian' if language == 'id' else 'English'} language."],
        show_tool_calls=True,
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
            if "429" in error_str or "503" in error_str or "quota" in error_str:
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
