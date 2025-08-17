from __future__ import annotations
from typing import Optional
from fastmcp import FastMCP, Context
from langfuse import get_client
from server.common.mcp_obs_middleware import trace_index, _pick_session_id


def register_feedback_tools(mcp: FastMCP):
    @mcp.tool(
        name="request_feedback",
        description="Elicit rating (1–5) + optional comment from the user and store as Langfuse score."
    )
    async def request_feedback(ctx: Context,
                               prompt: str = "Did that solve it? Provide rating 1–5 and an optional comment."):
        try:
            reply = await ctx.elicit(
                prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "rating": {"type": "number", "minimum": 1, "maximum": 5},
                        "comment": {"type": "string"}
                    },
                    "required": ["rating"]
                }
            )
        except Exception as e:
            return {"ok": False, "error": f"elicitation_failed: {e}", "next": "Call submit_feedback tool."}

        rating = float(reply.get("rating"))
        comment = (reply.get("comment") or "").strip()

        lf = get_client()
        sess = _pick_session_id(getattr(ctx.request, "headers", {}) or {})
        trace_id = trace_index.get(sess) or lf.get_current_trace_id()

        lf.create_score(name="user_rating", value=rating, trace_id=trace_id, comment=comment or None)
        if comment:
            lf.create_score(name="user_feedback_text", value=comment, trace_id=trace_id)
        return {"ok": True}

    @mcp.tool(
        name="submit_feedback",
        description="Directly submit rating/comment (used by UI or when elicitation is unavailable)."
    )
    async def submit_feedback(ctx: Context, rating: float, comment: str = "",
                              session_id: Optional[str] = None, trace_id: Optional[str] = None):
        lf = get_client()
        sess = session_id or _pick_session_id(getattr(ctx.request, "headers", {}) or {})
        tid = trace_id or trace_index.get(sess) or lf.get_current_trace_id()
        lf.create_score(name="user_rating", value=float(rating), trace_id=tid, comment=(comment or None))
        if comment:
            lf.create_score(name="user_feedback_text", value=comment, trace_id=tid)
        return {"ok": True}
