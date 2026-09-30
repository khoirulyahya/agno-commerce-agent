"""
MODULE 01: Hello Agno - Fastest Fundamental to Start Agno Agent
Run: python tutorials/01_hello_agno.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    description="You are LibraBot, a digital bookstore AI.",
    markdown=True
)

agent.print_response("Who are you and what do you do?", stream=True)
