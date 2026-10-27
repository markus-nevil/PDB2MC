import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  chooseStructure, Config, getConfig, getJob, getPlots, Job, Mode, Plot, startBuild, Structure,
} from "./api";

type Source = "rcsb" | "upload" | "preset";

function timeLeft(expires: number) {
  const seconds = Math.max(0, expires - Date.now() / 1000);
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  return hours > 0 ? `${hours} h ${minutes} min left` : `${minutes} min left`;
}

function CopyText({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="copy"
      title="Copy"
      onClick={() => {
        navigator.clipboard?.writeText(text).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 1500);
        });
      }}
    >
      <code>{text}</code>
      <span>{copied ? "Copied" : "Copy"}</span>
    </button>
  );
}

function StructurePicker({ config, onChosen }: { config: Config; onChosen: (s: Structure) => void }) {
  const [source, setSource] = useState<Source>("rcsb");
  const [pdbId, setPdbId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preset, setPreset] = useState("GFP");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const form = new FormData();
    if (source === "rcsb") form.append("pdb_id", pdbId.trim());
    else if (source === "upload" && file) form.append("file", file);
    else if (source === "preset") form.append("preset", preset);
    setBusy(true);
    setError("");
    try {
      onChosen(await chooseStructure(form));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const ready = source === "rcsb" ? /^[0-9][A-Za-z0-9]{3}$/.test(pdbId.trim())
    : source === "upload" ? file !== null : preset !== "";

  return (
    <form onSubmit={submit} className="picker">
      <div className="tabs" role="tablist">
        {([["rcsb", "PDB id"], ["upload", "Upload a file"], ["preset", "Example"]] as [Source, string][]).map(
          ([key, label]) => (
            <button key={key} type="button" role="tab" aria-selected={source === key}
              className={source === key ? "tab active" : "tab"} onClick={() => setSource(key)}>
              {label}
            </button>
          ),
        )}
      </div>
      {source === "rcsb" && (
        <label className="field">
          <span>4-character id from <a href="https://www.rcsb.org/" target="_blank" rel="noreferrer">rcsb.org</a></span>
          <input value={pdbId} onChange={(e) => setPdbId(e.target.value)} placeholder="e.g. 1EMA" maxLength={4}
            autoComplete="off" spellCheck={false} />
        </label>
      )}
      {source === "upload" && (
        <label className="field">
          <span>.pdb or .cif file, up to {config.limits.upload_mb} MB</span>
          <input type="file" accept=".pdb,.ent,.cif,.mmcif" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        </label>
      )}
      {source === "preset" && (
        <label className="field">
          <span>Structures that come with PDB2MC</span>
          <select value={preset} onChange={(e) => setPreset(e.target.value)}>
            {config.presets.map((p) => <option key={p}>{p}</option>)}
          </select>
        </label>
      )}
      <button className="primary" disabled={!ready || busy}>{busy ? "Reading…" : "Use this structure"}</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function BuildForm({ config, structure, onJob }: { config: Config; structure: Structure; onJob: (j: Job) => void }) {
  const [modeName, setModeName] = useState("Custom");
  const mode = useMemo(() => config.modes.find((m) => m.name === modeName) as Mode, [config, modeName]);
  const [options, setOptions] = useState<Record<string, boolean>>({});
  const [scale, setScale] = useState(structure.suggested_scale);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setOptions(Object.fromEntries(mode.options.map((o) => [o.key, o.default])));
  }, [mode]);
  useEffect(() => setScale(structure.suggested_scale), [structure]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      onJob(await startBuild(structure.token, mode.name, scale, options));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={submit}>
      <div className="modes">
        {config.modes.map((m) => (
          <label key={m.name} className={m.name === modeName ? "mode selected" : "mode"}>
            <input type="radio" name="mode" value={m.name} checked={m.name === modeName}
              onChange={() => setModeName(m.name)} />
            <strong>{m.name}</strong>
            <span>{m.description}</span>
          </label>
        ))}
      </div>
      <div className="settings">
        <label className="field scale">
          <span>Scale <output>{scale.toFixed(1)}×</output> <small>(1 block = {(1 / scale).toFixed(2)} Å; largest that fits: {structure.max_scale}×)</small></span>
          <input type="range" min={1} max={structure.max_scale} step={0.1} value={scale}
            onChange={(e) => setScale(Number(e.target.value))} />
        </label>
        <div className="options">
          {mode.options.map((o) => (
            <label key={o.key} className="check">
              <input type="checkbox" checked={options[o.key] ?? o.default}
                onChange={(e) => setOptions({ ...options, [o.key]: e.target.checked })} />
              {o.label}
            </label>
          ))}
        </div>
      </div>
      <button className="primary" disabled={busy}>{busy ? "Sending…" : "Build it in Minecraft"}</button>
      {error && <p className="error">{error}</p>}
    </form>
  );
}

function JobStatus({ job, config }: { job: Job; config: Config }) {
  if (job.status === "error") return <p className="error">{job.message}</p>;
  if (job.status !== "done" || !job.plot) {
    const label = job.status === "queued" && job.position ? `Waiting in line (position ${job.position})` : job.message;
    return (
      <div className="progress">
        <div className="bar"><div style={{ width: `${Math.max(3, job.progress)}%` }} /></div>
        <p>{label}…</p>
      </div>
    );
  }
  const plot = job.plot;
  return (
    <div className="result">
      <h3>Your model is on plot {plot.number}</h3>
      <ol>
        <li>Join <CopyText text={config.play_host} /> in Minecraft Java or Bedrock.</li>
        <li>Type <CopyText text={plot.command} /> to fly to it.</li>
      </ol>
      <p>
        <a className="button" href={plot.map_url} target="_blank" rel="noreferrer">See it on the 3D map</a>
        <span className="muted"> · {timeLeft(plot.expires)}</span>
      </p>
    </div>
  );
}

function PlotList({ plots }: { plots: Plot[] }) {
  if (!plots.length) return <p className="muted">No models yet. Be the first!</p>;
  return (
    <ul className="plots">
      {plots.map((p) => (
        <li key={p.number}>
          <span className="number">{p.number}</span>
          <span className="title" title={p.title}>{p.title}</span>
          <span className="muted">{p.mode} · {p.scale}× · {timeLeft(p.expires)}</span>
          <a href={p.map_url} target="_blank" rel="noreferrer">Map</a>
        </li>
      ))}
    </ul>
  );
}

export default function App() {
  const [config, setConfig] = useState<Config | null>(null);
  const [loadError, setLoadError] = useState("");
  const [structure, setStructure] = useState<Structure | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [plots, setPlots] = useState<Plot[]>([]);

  useEffect(() => {
    getConfig().then(setConfig).catch((e) => setLoadError((e as Error).message));
    const refresh = () => getPlots().then(setPlots).catch(() => undefined);
    refresh();
    const timer = setInterval(refresh, 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (!job || job.status === "done" || job.status === "error") {
      if (job?.status === "done") getPlots().then(setPlots).catch(() => undefined);
      return;
    }
    const timer = setTimeout(() => getJob(job.id).then(setJob).catch(() => undefined), 1500);
    return () => clearTimeout(timer);
  }, [job]);

  return (
    <>
      <header>
        <div className="brand">
          <img src="/logo.png" alt="" width={36} height={36} />
          <div>
            <h1>PDB2MC Builder</h1>
            <p>Proteins and DNA from the Protein Data Bank, built block by block in Minecraft.</p>
          </div>
        </div>
        {config && (
          <nav>
            <a href={config.map_url} target="_blank" rel="noreferrer">3D map</a>
            <a href={config.github_url} target="_blank" rel="noreferrer">PDB2MC on GitHub</a>
          </nav>
        )}
      </header>
      <main>
        {loadError && <p className="error">The builder is unavailable right now ({loadError}).</p>}
        {config && (
          <>
            <section className="card">
              <h2><span className="step">1</span> Choose a structure</h2>
              <StructurePicker config={config} onChosen={(s) => { setStructure(s); setJob(null); }} />
              {structure && (
                <p className="chosen">
                  <strong>{structure.title}</strong>
                  <span className="muted"> · {structure.atoms.toLocaleString()} atoms · {structure.chains} chain{structure.chains === 1 ? "" : "s"}</span>
                </p>
              )}
            </section>
            {structure && (
              <section className="card">
                <h2><span className="step">2</span> Choose a style</h2>
                <BuildForm config={config} structure={structure} onJob={setJob} />
                {job && <JobStatus job={job} config={config} />}
              </section>
            )}
            <section className="card">
              <h2>Join the world</h2>
              <div className="join">
                <div><strong>Java Edition</strong><CopyText text={config.play_host} /></div>
                <div><strong>Bedrock Edition</strong><CopyText text={config.play_host} /><small className="muted">port 19132</small></div>
              </div>
              <p className="muted">
                Visitors fly around as spectators. Type <code>/trigger plot set &lt;number&gt;</code> to visit a plot
                and <code>/trigger spawn</code> to come back. Models stay for {config.limits.plot_hours} hours.
              </p>
            </section>
            <section className="card">
              <h2>In the world now</h2>
              <PlotList plots={plots} />
            </section>
          </>
        )}
      </main>
      <footer className="muted">
        PDB2MC by Markus Nevil. Structures from the <a href="https://www.rcsb.org/" target="_blank" rel="noreferrer">RCSB Protein Data Bank</a>.
      </footer>
    </>
  );
}
