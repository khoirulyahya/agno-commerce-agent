"""
MODULE 04: LibraBot CLI - Complete Terminal Interaction
Run: python tutorials/04_librabot_cli.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.agent_factory import create_commerce_agent

print("=========================================")
print("🤖 LIBRABOT CLI - DIGITAL BOOKSTORE")
print("=========================================")
print("Type 'exit' or 'quit' to close.")

agent = create_commerce_agent(session_id="cli-demo")

while True:
    try:
        user_input = input("\nYou: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        print("\nLibraBot: ", end="")
        agent.print_response(user_input, stream=True)
    except KeyboardInterrupt:
        break
