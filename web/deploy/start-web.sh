#!/bin/sh
# Entry point of the web builder container (python:3.12-slim, running as uid 1000).
# /src is a checkout of this repository; dependencies live in a venv under /state, reinstalled
# only when requirements.txt changes.
set -e
REQ=/src/web/server/requirements.txt
VENV=/state/venv
STAMP="$VENV/.requirements-$(md5sum "$REQ" | cut -c1-12)"
if [ ! -f "$STAMP" ]; then
    python -m venv --clear "$VENV"
    "$VENV/bin/pip" install --quiet --no-cache-dir -r "$REQ"
    touch "$STAMP"
fi
export PYTHONPATH=/src:/src/web/server
export PDB2MC_STATIC_DIR=/src/web/frontend/dist
exec "$VENV/bin/python" -m pdb2mc_web
