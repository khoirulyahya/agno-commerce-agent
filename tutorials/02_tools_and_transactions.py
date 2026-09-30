"""
MODULE 02: Tools - Giving Hands to the Agent
Run: python tutorials/02_tools_and_transactions.py
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from agno.agent import Agent
from agno.models.google import Gemini

def search_book_catalog(keyword: str) -> str:
    """Search book catalog based on keyword."""
    if "python" in keyword.lower():
        return "Python Crash Course: Rp 95.000"
    return "Book not found."

agent = Agent(
    model=Gemini(id="gemini-2.5-flash"),
    tools=[search_book_catalog],
    instructions=["You are LibraBot. Help users find books."],
    show_tool_calls=True,
    markdown=True
)

agent.print_response("How much is the Python book?", stream=True)
