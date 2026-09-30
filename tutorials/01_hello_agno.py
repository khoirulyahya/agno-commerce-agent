"""
MODULE 01: Hello Agno - Fundamental Tercepat Memulai Agno Agent
Jalankan: python tutorials/01_hello_agno.py
"""
import sys
from pathlib import Path

# Load agent factory & Gemini Key Pool
sys.path.append(str(Path(__file__).parent.parent))
from src.agent_factory import create_commerce_agent

# 1. Buat Agent (Otomatis pakai Gemini Multi-Key Pool / Ollama)
agent = create_commerce_agent()

# 2. Jalankan Chat
print("--- TEST RESPONSE DARI RAPS-BOT ---")
agent.print_response("Halo! Kamu siapa dan bisa bantu apa saja di AgnoCommerce?", stream=True)
