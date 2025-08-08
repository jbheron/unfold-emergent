import axios from "axios";
import { useEffect, useState } from "react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard() {
  const [hello, setHello] = useState("");
  const [provider, setProvider] = useState(null);

  useEffect(() => {
    (async () => {
      try {
        const h = await axios.get(`${API}/`);
        setHello(h.data?.message || "");
      } catch {}
      try {
        const p = await axios.get(`${API}/provider-info`);
        setProvider(p.data);
      } catch {}
    })();
  }, []);

  return (
    <div>
      <header className="App-header">
        <a className="App-link" href="https://emergent.sh" target="_blank" rel="noopener noreferrer">
          <img src="https://avatars.githubusercontent.com/in/1201222?s=120&amp;u=2686cf91179bbafbc7a71bfbc43004cf9ae1acea&amp;v=4" />
        </a>
        <p className="mt-5">Building something incredible ~!</p>
      </header>

      <section className="panel">
        <div className="cards-grid">
          <a className="card-link" href="/story">
            <div className="card-tile">
              <h3>My Story</h3>
              <p>Create and evolve your living story. Autosave + resonance.</p>
            </div>
          </a>
          <a className="card-link" href="/coach">
            <div className="card-tile">
              <h3>Coach</h3>
              <p>Talk with FAM for reflective support and gentle prompts.</p>
            </div>
          </a>
        </div>
      </section>

      <section className="panel">
        <div className="info-box">
          <div>Backend hello: <strong>{hello || "..."}</strong></div>
          <div className="muted">Provider: {provider?.provider || "-"} ({provider?.model || "-"})</div>
        </div>
      </section>
    </div>
  );
}