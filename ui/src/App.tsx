import { useState } from "react";
const FEEDBACK_URL = import.meta.env.VITE_FEEDBACK_URL!;
const urlSession = new URLSearchParams(location.search).get("session_id") ?? "";

export default function App() {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [sessionId, setSessionId] = useState(urlSession);
  const [sending, setSending] = useState(false);
  const [ok, setOk] = useState<boolean | null>(null);

  async function submit() {
    setSending(true); setOk(null);
    const payload: any = { rating, comment };
    if (sessionId) payload.session_id = sessionId;
    const res = await fetch(FEEDBACK_URL, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    setOk(res.ok); setSending(false);
  }

  return (
    <div style={{ maxWidth: 560, margin: "40px auto", fontFamily: "system-ui, sans-serif" }}>
      <h1>MCP Run Feedback</h1>
      <div style={{ display: "flex", gap: 8, margin: "6px 0 16px" }}>
        {[1,2,3,4,5].map(n => (
          <button key={n} onClick={() => setRating(n)}
            style={{ width: 44, height: 44, borderRadius: 8, border: "1px solid #ccc",
                     background: n <= rating ? "#ffd966" : "white" }}>{n}</button>
        ))}
      </div>
      <textarea value={comment} onChange={e=>setComment(e.target.value)}
        placeholder="What worked? What didn’t?" rows={5}
        style={{ width:"100%", padding:10, borderRadius:8, border:"1px solid #ccc", marginBottom:12 }} />
      <details style={{ marginBottom: 12 }}>
        <summary>Advanced</summary>
        <label>Session ID (optional)</label>
        <input value={sessionId} onChange={e=>setSessionId(e.target.value)}
          placeholder="Mcp-Session-Id; leave empty to auto-resolve"
          style={{ width:"100%", padding:10, borderRadius:8, border:"1px solid #ccc" }}/>
      </details>
      <button disabled={sending} onClick={submit}
        style={{ padding:"10px 16px", borderRadius:8, border:"1px solid #333", background:"#111", color:"#fff" }}>
        {sending ? "Sending…" : "Send feedback"}
      </button>
      {ok === true && <p style={{ color:"green", marginTop:12 }}>Thanks! Saved.</p>}
      {ok === false && <p style={{ color:"crimson", marginTop:12 }}>Failed to save.</p>}
    </div>
  );
}
