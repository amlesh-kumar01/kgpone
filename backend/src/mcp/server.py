from fastmcp import FastMCP

mcp = FastMCP("KgpOne Agent Server")

@mcp.tool()
def hello_tool() -> str:
    """A simple tool to say hello."""
    return "Hello from KgpOne FastMCP!"
