import { useEffect, useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CoachChat() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState(null);
  const [error, setError] = useState(null);

  const fetchProvider = async () => {
    try {
      const { data } = await axios.get(`${API}/provider-info`);
      setProviderInfo(data);
    } catch (e) {
      console.error("provider-info failed", e);
    }
  };

  useEffect(() => { fetchProvider(); }, []);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const newMsgs = [...messages, { role: "user", content: input.trim() }];
    setMessages(newMsgs);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const { data } = await axios.post(`${API}/chat`, {
        messages: newMsgs,
        temperature: 0.7,
        max_tokens: 600,
      });
      setMessages([...newMsgs, data.message]);
    } catch (e) {
      const detail = e?.response?.data?.detail || e.message;
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="chat-wrap">
      <div className="chat-head">
        <div>
          <h2>FAM • AI Coach</h2>
          <p className="muted">Provider: {providerInfo?.provider || "unknown"} ({providerInfo?.model || "-"})</p>
        </div>
      </div>
      <div className="chat-body">
        {messages.length === 0 && (
          <div className="assistant msg">
            <div className="bubble">Hello! I'm here to support your reflection and growth. What's on your mind today?</div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`${m.role === "user" ? "user" : "assistant"} msg`}>
            <div className="bubble">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="assistant msg">
            <div className="bubble typing"><span></span><span></span><span></span></div>
          </div>
        )}
        {error && (<div className="error">{error}</div>)}
      </div>
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          rows={2}
          placeholder="Type your message..."
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
            }
          }}
        />
        <button disabled={loading || !input.trim()} onClick={sendMessage}>{loading ? "..." : "Send"}</button>
      </div>
    </div>
  );
}