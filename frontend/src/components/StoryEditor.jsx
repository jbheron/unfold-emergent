import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const defaultSections = {
  guidingNarrative: "",
  turningPoints: "",
  emergingThemes: "",
  uniqueStrengths: "",
  futureVision: "",
};

const useDebounced = (fn, delay = 1200) => {
  const timeout = useRef(null);
  return (...args) => {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = setTimeout(() => fn(...args), delay);
  };
};

export default function StoryEditor() {
  const [clientId, setClientId] = useState("");
  const [story, setStory] = useState(null);
  const [sections, setSections] = useState(defaultSections);
  const [resonance, setResonance] = useState(5);
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cid = localStorage.getItem("client_id");
    if (!cid) {
      cid = (crypto && crypto.randomUUID) ? crypto.randomUUID() : Math.random().toString(36).slice(2);
      localStorage.setItem("client_id", cid);
    }
    setClientId(cid);
  }, []);

  useEffect(() => {
    if (!clientId) return;
    (async () => {
      try {
        const { data } = await axios.post(`${API}/story/init`, { clientId });
        setStory(data);
        setSections(data.sections || defaultSections);
        if (typeof data.resonanceScore === "number") setResonance(data.resonanceScore);
      } catch (e) {
        setError(e?.response?.data?.detail || e.message);
      }
    })();
  }, [clientId]);

  const save = async (next) => {
    if (!story) return;
    setSaving(true);
    setError(null);
    try {
      const { data } = await axios.put(`${API}/story/save`, {
        storyId: story.storyId,
        clientId,
        sections: next.sections,
        resonanceScore: next.resonance,
      });
      setStory(data);
      setLastSaved(new Date());
    } catch (e) {
      setError(e?.response?.data?.detail || e.message);
    } finally {
      setSaving(false);
    }
  };

  const debouncedSave = useDebounced((nextState) => save(nextState), 1200);

  const onChange = (key, value) => {
    const nextSections = { ...sections, [key]: value };
    setSections(nextSections);
    debouncedSave({ sections: nextSections, resonance });
  };

  const onResChange = (v) => {
    const next = Number(v);
    setResonance(next);
    debouncedSave({ sections, resonance: next });
  };

  return (
    <div className="story-wrap">
      <div className="story-head">
        <div>
          <h2>My Story</h2>
          <p className="muted">A living document. Autosaves as you type.</p>
        </div>
        <div className="save-state">
          {saving ? <span className="dot"/> : <span className="dot ok"/>}
          <span>{saving ? "Saving..." : lastSaved ? `Saved ${lastSaved.toLocaleTimeString()}` : "Synced"}</span>
          {story && <span className="ver">v{story.version}</span>}
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="resonance-row">
        <label>Resonance</label>
        <input type="range" min="0" max="10" step="0.5" value={resonance} onChange={(e) => onResChange(e.target.value)} />
        <div className="res-val">{resonance}</div>
      </div>

      <div className="grid">
        <Section title="Guiding Narrative" value={sections.guidingNarrative} onChange={(v) => onChange("guidingNarrative", v)} />
        <Section title="Turning Points" value={sections.turningPoints} onChange={(v) => onChange("turningPoints", v)} />
        <Section title="Emerging Themes" value={sections.emergingThemes} onChange={(v) => onChange("emergingThemes", v)} />
        <Section title="Unique Strengths" value={sections.uniqueStrengths} onChange={(v) => onChange("uniqueStrengths", v)} />
        <Section title="Future Vision" value={sections.futureVision} onChange={(v) => onChange("futureVision", v)} />
      </div>
    </div>
  );
}

function Section({ title, value, onChange }) {
  return (
    <div className="card">
      <div className="card-head">
        <h4>{title}</h4>
      </div>
      <textarea
        className="card-input"
        rows={6}
        placeholder={`Write about ${title.toLowerCase()}...`}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}