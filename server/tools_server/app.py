import uvicorn
from fastmcp import FastMCP
from fastmcp.server.http import create_streamable_http_app
from starlette.middleware import Middleware
from server.common.mcp_obs_middleware import MCPObservabilityMiddleware
from .tools import register_dummy_tools

mcp = FastMCP("DemoMCP-Tools")
register_dummy_tools(mcp)

app = create_streamable_http_app(
    server=mcp,
    streamable_http_path="/mcp",
    middleware=[Middleware(MCPObservabilityMiddleware)],
    debug=True,
)

if __name__ == "__main__":
    uvicorn.run("server.tools_server.app:app", host="0.0.0.0", port=3002, reload=True)
