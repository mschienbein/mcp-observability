import uvicorn
from fastmcp import FastMCP
from fastmcp.server.http import create_streamable_http_app
from starlette.middleware import Middleware
from mcp_local.common import config  # Load environment variables
from mcp_local.common.mcp_obs_middleware import MCPObservabilityMiddleware
from .feedback_tools import register_feedback_tools

mcp = FastMCP("DemoMCP-Feedback")
register_feedback_tools(mcp)

app = create_streamable_http_app(
    server=mcp,
    streamable_http_path="/mcp",
    middleware=[Middleware(MCPObservabilityMiddleware)],
    debug=True,
)

if __name__ == "__main__":
    uvicorn.run("mcp_local.feedback_server.main:app", host="0.0.0.0", port=3003, reload=True)
