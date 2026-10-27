export type Option = { key: string; label: string; default: boolean };
export type Mode = { name: string; description: string; options: Option[] };
export type Config = {
  modes: Mode[];
  presets: string[];
  limits: { upload_mb: number; plot_hours: number; builds_per_hour: number; max_plots: number };
  play_host: string;
  map_url: string;
  github_url: string;
};
export type Structure = {
  token: string;
  title: string;
  source: string;
  atoms: number;
  chains: number;
  max_scale: number;
  suggested_scale: number;
};
export type Plot = {
  number: number;
  title: string;
  mode: string;
  scale: number;
  created: number;
  expires: number;
  blocks: number;
  center: [number, number];
  command: string;
  map_url: string;
};
export type Job = {
  id: string;
  status: "queued" | "building" | "placing" | "done" | "error";
  progress: number;
  message: string;
  position: number | null;
  plot: Plot | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* not JSON */
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}

export const getConfig = () => request<Config>("/api/config");
export const getPlots = () => request<Plot[]>("/api/plots");
export const getJob = (id: string) => request<Job>(`/api/builds/${id}`);

export function chooseStructure(form: FormData) {
  return request<Structure>("/api/structures", { method: "POST", body: form });
}

export function startBuild(token: string, mode: string, scale: number, options: Record<string, boolean>) {
  return request<Job>("/api/builds", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, mode, scale, options }),
  });
}
