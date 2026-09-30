"""
MODULE 03: Memory & Multi-Turn Sessions
Jalankan: python tutorials/03_memory_and_sessions.py

Pelajaran Penting:
Bagaimana Agent mengingat riwayat chat customer (seperti nomor ID ML atau paket yang tadi dipilih)
tanpa memaksa user login.
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from src.agent_factory import create_commerce_agent

agent = create_commerce_agent()

print("\n--- TURN 1: User mengenalkan ID Game-nya ---")
agent.print_response("Halo kak, catat ya ID ML ku 77381928 dan Zone 2026", stream=False)

print("\n--- TURN 2: User memesan tanpa mengulang ID Game ---")
agent.print_response("Sekarang tolong buatkan order 86 diamond ke akun yang tadi!", stream=False)
