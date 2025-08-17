from __future__ import annotations
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from langfuse import get_client
from .trace_index import get_trace_index

# Shared trace index instance (memory or Redis depending on env)
trace_index = get_trace_index()

def _pick_session_id(h) -> Optional[str]:
    return (h.get("Mcp-Session-Id") or h.get("X-MCP-Session-Id")
            or h.get("X-Session-Id") or h.get("Session-Id")
            or h.get("X-Client-Session-Id"))

def _pick_user_id(h) -> Optional[str]:
    return (h.get("X-User-Id") or h.get("X-GitHub-User") or h.get("X-Microsoft-User"))

class MCPObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        lf = get_client()
        sess = _pick_session_id(request.headers)
        user = _pick_user_id(request.headers)

        with lf.start_as_current_span(name=f"mcp:{request.url.path}") as span:
            if sess or user:
                span.update_trace(session_id=sess, user_id=user, tags=["mcp"])
            trace_id = lf.get_current_trace_id()
            if sess and trace_id:
                trace_index.set(sess, trace_id)
            resp: Response = await call_next(request)
            return resp
