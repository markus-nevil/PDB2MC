"""Settings of the PDB2MC web builder, read from environment variables."""
import os


def _env(name, default, cast=str):
    value = os.environ.get(name)
    return default if value in (None, "") else cast(value)


# Minecraft server data folder (itzg/minecraft-server's /data) and the world inside it
DATA_DIR = _env("PDB2MC_DATA_DIR", "/data")
WORLD_NAME = _env("PDB2MC_WORLD", "world")
WORLD_DIR = os.path.join(DATA_DIR, WORLD_NAME)
# Builder state: plots.json, uploads, model input files
STATE_DIR = _env("PDB2MC_STATE_DIR", "/state")
# Built frontend (web/frontend/dist)
STATIC_DIR = _env("PDB2MC_STATIC_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist"))

RCON_HOST = _env("RCON_HOST", "minecraft")
RCON_PORT = _env("RCON_PORT", 25575, int)
RCON_PASSWORD = _env("RCON_PASSWORD", "")

# Plots: square areas of PLOT_SIZE blocks, PLOT_PITCH apart, PLOTS_PER_ROW to a row, away from spawn
PLOT_SIZE = _env("PDB2MC_PLOT_SIZE", 256, int)
PLOT_PITCH = _env("PDB2MC_PLOT_PITCH", 320, int)
PLOTS_PER_ROW = _env("PDB2MC_PLOTS_PER_ROW", 8, int)
MAX_PLOTS = _env("PDB2MC_MAX_PLOTS", 40, int)
PLOT_HOURS = _env("PDB2MC_PLOT_HOURS", 48, float)
# Superflat ground: players stand at GROUND_Y; blocks may go up to TOP_Y
GROUND_Y = _env("PDB2MC_GROUND_Y", -60, int)
TOP_Y = _env("PDB2MC_TOP_Y", 319, int)

# Limits for public use
MAX_UPLOAD_MB = _env("PDB2MC_MAX_UPLOAD_MB", 20, float)
MAX_ATOMS = _env("PDB2MC_MAX_ATOMS", 150_000, int)
MAX_SCALE = _env("PDB2MC_MAX_SCALE", 10.0, float)
MAX_BLOCKS = _env("PDB2MC_MAX_BLOCKS", 1_500_000, int)
BUILD_TIMEOUT = _env("PDB2MC_BUILD_TIMEOUT", 240, int)
BUILDS_PER_HOUR = _env("PDB2MC_BUILDS_PER_HOUR", 4, int)
UPLOADS_PER_HOUR = _env("PDB2MC_UPLOADS_PER_HOUR", 30, int)
# Requests from these addresses (the cloudflared connector) carry the visitor's address in
# CF-Connecting-IP; from anywhere else the header is ignored
TRUSTED_PROXIES = {ip.strip() for ip in _env("PDB2MC_TRUSTED_PROXIES", "").split(",") if ip.strip()}

# Shown to visitors
PLAY_HOST = _env("PDB2MC_PLAY_HOST", "play.pdb2mc.com")
MAP_URL = _env("PDB2MC_MAP_URL", "https://map.pdb2mc.com").rstrip("/")
GITHUB_URL = _env("PDB2MC_GITHUB_URL", "https://github.com/markus-nevil/PDB2MC")
RCSB_DOWNLOAD = _env("PDB2MC_RCSB_DOWNLOAD", "https://files.rcsb.org/download/{id}.cif")
