# PDB2MC web builder

The site behind **build.pdb2mc.com**: visitors pick a structure (RCSB PDB id, upload, or an included
example), choose a PDB2MC mode, and the model is built on a plot of a shared Minecraft server
(**play.pdb2mc.com**, Java and Bedrock). Plots are cleared after 48 hours. **map.pdb2mc.com** is BlueMap.

- `server/pdb2mc_web/` – FastAPI app. Builds run through `PDB2MC.build.build_model` in a child process
  (one at a time, with a timeout); models are placed with RCON
  (`execute positioned <plot> run function protein:build_<name>` while the plot is force-loaded).
  Players reach a plot with `/trigger plot set <n>` (a small `plots` datapack written by the builder).
- `frontend/` – React + Vite page, served by the API.
- Structures that visitors build (uploads and RCSB downloads) are kept in `<state>/library`, stored once
  per file content, and offered to later visitors ("Saved by visitors"). An identical model (same file,
  mode, scale and options) is not built twice: the visitor is sent to its plot and its timer restarts.
- `deploy/` – container entry point and a compose template. The server runs the latest GitHub release:
  restarting the app checks out the newest release tag (and rebuilds the frontend).
- `tests/` – `python -m pytest web/tests` (uses a fake Minecraft console).

Run locally: `pip install -r web/server/requirements.txt`, build the frontend (`npm ci && npm run build` in
`frontend/`), then `PYTHONPATH=.:web/server RCON_HOST=... RCON_PASSWORD=... python -m pdb2mc_web`.
