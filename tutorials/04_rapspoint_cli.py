"""
MODULE 04: Interactive Terminal CLI for AgnoCommerce Agent
Jalankan: python tutorials/04_agno-commerce_cli.py

Coba ketik:
1. "Berapa harga diamond ML?"
2. "Mau beli 86 diamond untuk ID 88392019 zone 2102"
3. "Tolong cek invoice INV-9921"
4. "Berapa harga joki dari Epic ke Mythic?"
"""
import sys
from pathlib import Path

# Add parent directory to sys.path
sys.path.append(str(Path(__file__).parent.parent))

from src.agent_factory import create_commerce_agent

def main():
    print("=" * 60)
    print("🎮 AgnoCommerce ID - AGNO TERMINAL CHATBOT 🎮")
    print("Ketik pesan Anda di bawah atau ketik 'exit' untuk keluar.")
    print("=" * 60)
    
    agent = create_commerce_agent()
    
    while True:
        try:
            user_msg = input("\n👤 Customer: ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ["exit", "quit", "keluar"]:
                print("👋 Terima kasih telah bertransaksi di AgnoCommerce!")
                break
                
            print("\n🤖 RAPS-BOT:")
            agent.print_response(user_msg, stream=True)
            print()
        except KeyboardInterrupt:
            print("\n👋 Sesi selesai.")
            break

if __name__ == "__main__":
    main()
