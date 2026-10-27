"""
HTTP API of the PDB2MC web builder (served at build.pdb2mc.com), plus the built frontend.

  GET  /api/config            modes, options, presets, limits and addresses to show
  POST /api/structures        choose a structure: multipart `file`, or form field `pdb_id` or `preset`
  POST /api/builds            {token, mode, scale, options} -> build job
  GET  /api/builds/{id}       job status (and the plot when done)
  GET  /api/plots             models currently in the world
  GET  /api/health
"""
import collections
import logging
import os
import threading
import time

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from PDB2MC import defaults

from . import inputs, settings
from .jobs import MODE_OPTIONS, Builder
from .rcon import Rcon
from .store import PlotStore
from .world import World

log = logging.getLogger(__name__)

MODE_DESCRIPTIONS = {
    "Custom": "Atoms as coloured spheres with the backbone and sidechains inside.",
    "Skeleton": "Only the bonds: backbone and sidechains.",
    "X-Ray": "See-through glass atoms around a solid skeleton.",
    "Space Filling": "The solvent accessible surface, with the skeleton inside.",
    "Ribbon": "Cartoon ribbons for helices and sheets, coloured by chain.",
    "Amino Acids": "One coloured ball per amino acid along the backbone.",
}
OPTION_LABELS = {"by_chain": "Colour by chain", "backbone": "Show backbone", "sidechain": "Show sidechains",
                 "show_hetatm": "Show other molecules (ligands, ions)", "mesh": "Mesh style (fewer blocks)",
                 "bar_style": "Helices as rods"}


class RateLimiter:
    """At most `limit` events per client in a sliding hour."""

    def __init__(self, limit, window=3600):
        self.limit, self.window = limit, window
        self._events = collections.defaultdict(collections.deque)
        self._lock = threading.Lock()

    def hit(self, client):
        now = time.time()
        with self._lock:
            events = self._events[client]
            while events and events[0] <= now - self.window:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True


class BuildRequest(BaseModel):
    token: str = Field(max_length=64)
    mode: str
    scale: float
    options: dict = {}


def client_address(request: Request):
    host = request.client.host if request.client else "unknown"
    if host in settings.TRUSTED_PROXIES:
        return request.headers.get("cf-connecting-ip", host)
    return host


def create_app(builder=None):
    if builder is None:
        os.makedirs(settings.STATE_DIR, exist_ok=True)
        rcon = Rcon(settings.RCON_HOST, settings.RCON_PORT, settings.RCON_PASSWORD)
        builder = Builder(World(rcon), PlotStore())
        builder.start()
    uploads = RateLimiter(settings.UPLOADS_PER_HOUR)
    builds = RateLimiter(settings.BUILDS_PER_HOUR)
    app = FastAPI(title="PDB2MC builder", docs_url=None, redoc_url=None)
    app.state.builder = builder

    @app.get("/api/health")
    def health():
        return {"minecraft": builder.ready, "error": builder.last_error}

    @app.get("/api/config")
    def config():
        return {
            "modes": [{"name": m, "description": MODE_DESCRIPTIONS[m],
                       "options": [{"key": k, "label": OPTION_LABELS[k],
                                    "default": bool(defaults.default_config(m)[k])} for k in MODE_OPTIONS[m]]}
                      for m in defaults.MODES],
            "presets": inputs.presets(),
            "limits": {"upload_mb": settings.MAX_UPLOAD_MB, "plot_hours": settings.PLOT_HOURS,
                       "builds_per_hour": settings.BUILDS_PER_HOUR, "max_plots": settings.MAX_PLOTS},
            "play_host": settings.PLAY_HOST, "map_url": settings.MAP_URL, "github_url": settings.GITHUB_URL,
        }

    @app.post("/api/structures")
    def choose_structure(request: Request, file: UploadFile | None = File(None),
                         pdb_id: str | None = Form(None), preset: str | None = Form(None)):
        if not uploads.hit(client_address(request)):
            raise HTTPException(429, "Too many structures chosen; please wait a while.")
        try:
            if file is not None and file.filename:
                summary = inputs.from_upload(file.filename, file.file)
            elif pdb_id:
                summary = inputs.from_pdb_id(pdb_id)
            elif preset:
                summary = inputs.from_preset(preset)
            else:
                raise inputs.InputError("Choose a file, a PDB id or a preset.")
        except inputs.InputError as e:
            raise HTTPException(400, str(e))
        return {k: summary[k] for k in ("token", "title", "source", "atoms", "chains", "max_scale",
                                         "suggested_scale")}

    @app.post("/api/builds")
    def start_build(body: BuildRequest, request: Request):
        client = client_address(request)
        if not builder.ready:
            raise HTTPException(503, "The Minecraft server is starting; please try again in a minute.")
        if not builds.hit(client):
            raise HTTPException(429, f"You can build {settings.BUILDS_PER_HOUR} models per hour; please wait.")
        try:
            job = builder.submit(body.token, body.mode, body.scale, body.options, client)
        except inputs.InputError as e:
            raise HTTPException(400, str(e))
        return builder.status(job.id)

    @app.get("/api/builds/{job_id}")
    def build_status(job_id: str):
        status = builder.status(job_id)
        if status is None:
            raise HTTPException(404, "Unknown build.")
        return status

    @app.get("/api/plots")
    def plots():
        return builder.plots()

    static = os.path.abspath(settings.STATIC_DIR)
    if os.path.isdir(static):
        app.mount("/assets", StaticFiles(directory=os.path.join(static, "assets")), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str):
            target = os.path.abspath(os.path.join(static, path))
            if path and target.startswith(static + os.sep) and os.path.isfile(target):
                return FileResponse(target)
            return FileResponse(os.path.join(static, "index.html"))

    return app


def main():
    import uvicorn
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8000")),
                forwarded_allow_ips="*", proxy_headers=False)


if __name__ == "__main__":
    main()
