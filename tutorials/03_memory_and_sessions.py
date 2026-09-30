"""
MODULE 03: Memory - Making the Agent Remember Context
Run: python tutorials/03_memory_and_sessions.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    add_history_to_messages=True,
    session_id="user-123",
    markdown=True
)

print("--- Chat 1 ---")
agent.print_response("Hi, my name is John and I like Python.", stream=True)

print("\n--- Chat 2 ---")
agent.print_response("What is my name and what do I like?", stream=True)
