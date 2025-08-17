import uvicorn
from fastapi import FastAPI
from fastmcp import FastMCP
from fastmcp.server.http import create_streamable_http_app
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from langfuse import get_client
from server.common.mcp_obs_middleware import MCPObservabilityMiddleware, _pick_session_id, _pick_user_id, trace_index
from .feedback_tools import register_feedback_tools

# Build MCP sub-app
mcp = FastMCP("DemoMCP-Feedback")
register_feedback_tools(mcp)
mcp_app = create_streamable_http_app(
    server=mcp,
    streamable_http_path="/mcp",
    middleware=[Middleware(MCPObservabilityMiddleware)],
    debug=True,
)

# Root API app: mount MCP and expose REST feedback endpoint
app = FastAPI(middleware=[
    Middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"] ),
])
app.mount("/", mcp_app)

@app.post("/api/feedback")
async def submit_feedback_rest(request: Request):
    payload = await request.json()
    rating = float(payload.get("rating"))
    comment = (payload.get("comment") or "").strip()
    lf = get_client()
    sess = payload.get("session_id") or _pick_session_id(request.headers)
    user = _pick_user_id(request.headers)
    with lf.start_as_current_span(name="mcp:/api/feedback") as span:
        if sess or user:
            span.update_trace(session_id=sess, user_id=user, tags=["mcp"])  # align with middleware behavior
        trace_id = trace_index.get(sess) or lf.get_current_trace_id()
        if sess and trace_id:
            trace_index.set(sess, trace_id)
        lf.create_score(name="user_rating", value=rating, trace_id=trace_id, comment=(comment or None))
        if comment:
            lf.create_score(name="user_feedback_text", value=comment, trace_id=trace_id)
    return JSONResponse({"ok": True})

if __name__ == "__main__":
    uvicorn.run("server.feedback_server.app:app", host="0.0.0.0", port=3003, reload=True)
