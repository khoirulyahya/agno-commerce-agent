"""
MODULE 02: Tools & Function Calling - Cara AI Mengeksekusi Aksi Nyata
Jalankan: python tutorials/02_tools_and_transactions.py

Pelajaran Penting:
1. Fungsi Python biasa dengan type hints (user_id: str, amount: int) + Docstring
2. Agno otomatis membaca Docstring sebagai instruksi untuk LLM (kapan dan cara manggil fungsi).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.agent_factory import create_commerce_agent

# 1. Gunakan Agent yang sudah dilengkapi Tools Transaksi AgnoCommerce
agent = create_commerce_agent()

# 2. Test Eksekusi Tool Cek Katalog
print("\n--- TEST 1: USER BERTANYA HARGA DIAMOND MLBB ---")
agent.print_response("Berapa harga 86 diamond Mobile Legends hari ini?", stream=True)

# 3. Test Eksekusi Tool Pembuatan Invoice Order
print("\n\n--- TEST 2: USER ORDER TOP UP ---")
agent.print_response("Saya mau order 86 diamond dong, ID ku 88491029 zone 2102 bayar QRIS", stream=True)
