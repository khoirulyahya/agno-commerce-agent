from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun

# bikin instance dari LangChain tool
duckduckgo = DuckDuckGoSearchRun()

# bungkus biar jadi Agno tool
@tool
def search_duckduckgo(query: str) -> str:
    """Cari informasi di internet pakai DuckDuckGo"""
    return duckduckgo.run(query)

# bikin agent
agent = Agent(
    model=Ollama(id="llama3.1"),
    tools=[search_duckduckgo]
)

# Jalankan
agent.print_response(
    "Cari berita tentang AI terbaru di internet dan ringkas dalam 3 poin utama.",
    stream=True,
    show_tool_calls=True,
    show_full_reasoning=True,
    markdown=True
)
