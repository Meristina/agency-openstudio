import { useEffect, useState } from "react";
import { clearCapability, fetchCapabilities, selectCapability } from "../api";
import type { CapabilityInventory, Family } from "../types";

function badge(text: string, tone = "") {
  return <span className={`badge ${tone}`}>{text}</span>;
}

const reasonLabels: Record<string, string> = {
  missing_binary: "Missing binary",
  missing_model_files: "Missing model files",
  model_files_mismatch: "Model file mismatch",
  gateway_down: "Gateway down",
};

export default function Capabilities() {
  const [inventory, setInventory] = useState<CapabilityInventory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const refresh = async (force = false) => {
    setBusy(true);
    setError(null);
    try {
      setInventory(await fetchCapabilities(force));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, []);

  const choose = async (family: Family, id: string) => {
    setBusy(true);
    setError(null);
    try {
      if (id) await selectCapability(family, id);
      else await clearCapability(family);
      setInventory(await fetchCapabilities());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="panel capabilities-panel">
      <div className="row between">
        <h2>Capabilities</h2>
        <button className="ghost" onClick={() => void refresh(true)} disabled={busy}>
          Refresh
        </button>
      </div>
      {error && <p className="error">{error}</p>}
      {!inventory && !error && <p className="muted">Loading…</p>}
      {inventory?.families.map((family) => (
        <section className="cap-family" key={family.family}>
          <div className="row between">
            <h3>{family.family}</h3>
            <div className="row">
              {family.env_override && badge(`overridden by $${family.env_override}`, "warn")}
              {family.selected_stale && badge("stale selection", "warn")}
              {family.active && badge(`active: ${family.active}`, "ok")}
            </div>
          </div>
          {family.selectable && (
            <label className="field">
              <span className="field-label">Default</span>
              <select
                className="model-select"
                value={family.selected ?? ""}
                disabled={busy}
                onChange={(e) => void choose(family.family, e.target.value)}
              >
                <option value="">Built-in default</option>
                {family.selected && !family.entries.some((entry) => entry.id === family.selected) && (
                  <option value={family.selected} disabled>
                    {family.selected} (no longer available)
                  </option>
                )}
                {family.entries.map((entry) => (
                  <option key={entry.id} value={entry.id} disabled={entry.availability !== "available"}>
                    {entry.label}
                  </option>
                ))}
              </select>
            </label>
          )}
          <div className="cap-list">
            {family.entries.length === 0 && <p className="muted">No entries configured.</p>}
            {family.entries.map((entry) => (
              <article className="cap-entry" key={entry.id}>
                <div className="row between">
                  <strong>{entry.label}</strong>
                  <div className="row">
                    {badge(entry.cost === "free_paid" ? "FREE/PAID" : entry.cost.toUpperCase())}
                    {entry.tier && badge(entry.tier)}
                    {badge(entry.availability.toUpperCase(), entry.availability === "available" ? "ok" : "warn")}
                    {entry.default && badge("default")}
                  </div>
                </div>
                <code>{entry.id}</code>
                {entry.note && <p className="hint">{entry.note}</p>}
                {entry.availability === "unavailable" && (
                  <p className="error">
                    {reasonLabels[entry.reason ?? ""] ?? entry.reason}: {entry.enablement}
                  </p>
                )}
              </article>
            ))}
          </div>
        </section>
      ))}
    </section>
  );
}
