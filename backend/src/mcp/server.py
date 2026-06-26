from fastmcp import FastMCP
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP(
    "KgpOne Academic Knowledge Server",
    instructions="You are connected to KgpOne, a university knowledge platform. Use the provided tools to query the catalog, documents, knowledge graph, and perform hybrid RAG."
)

from src.mcp.tools import register_tools
from src.mcp.prompts import register_prompts

register_tools(mcp)
register_prompts(mcp)
