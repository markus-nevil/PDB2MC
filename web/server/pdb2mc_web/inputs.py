"""
Structures chosen by visitors: an uploaded file, an RCSB PDB id or one of PDB2MC's presets. Each is
saved under <state>/uploads/<token>.<ext> with a <token>.json summary, and builds refer to the token.
"""
import hashlib
import json
import math
import os
import re
import secrets
import shutil
import time

import httpx

from PDB2MC import build, pdb_manipulation as pdbm, resources

from . import library, settings

EXTENSIONS = (".pdb", ".ent", ".cif", ".mmcif")
PDB_ID = re.compile(r"^[0-9][A-Za-z0-9]{3}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
# Extra room (in Angstrom at scale 1) around the atoms: atom spheres and the space filling surface
SIZE_MARGIN = 8


class InputError(ValueError):
    """A problem with the visitor's input; the message is shown to them."""


def uploads_dir():
    path = os.path.join(settings.STATE_DIR, "uploads")
    os.makedirs(path, exist_ok=True)
    return path


def presets():
    return sorted(os.path.splitext(f)[0] for f in os.listdir(resources.presets_dir()) if f.lower().endswith(".pdb"))


def max_scale(structure):
    """Largest scale (one decimal) at which the model fits on a plot and below the build height."""
    df = build.prepare_coordinates(structure, 1.0)
    extent = (df[['X', 'Y', 'Z']].max() - df[['X', 'Y', 'Z']].min() + 1).to_dict()
    by_height = (settings.TOP_Y - settings.GROUND_Y) / (extent['Y'] + SIZE_MARGIN)
    by_width = settings.PLOT_SIZE / (max(extent['X'], extent['Z']) + SIZE_MARGIN)
    return math.floor(min(by_height, by_width, settings.MAX_SCALE) * 10) / 10


def _summarise(path, source):
    try:
        structure = pdbm.load_structure(path)
        atoms = len(structure.atoms)
    except Exception as e:
        raise InputError(f"Could not read this structure file ({type(e).__name__}).") from e
    if atoms == 0:
        raise InputError("The file contains no atoms.")
    if atoms > settings.MAX_ATOMS:
        raise InputError(f"This structure has {atoms:,} atoms; the limit is {settings.MAX_ATOMS:,}.")
    largest = max_scale(structure)
    if largest < 1:
        raise InputError("This structure is too large to fit on a plot.")
    title = " ".join(str(structure.metadata.get('title') or '').split()) or source
    return {"title": title[:200], "source": source, "atoms": atoms, "chains": len(structure.sequences),
            "max_scale": largest, "suggested_scale": min(largest, max(1.0, math.floor(largest / 2)))}


def _store(path, ext, source, kind):
    token = secrets.token_urlsafe(18)
    target = os.path.join(uploads_dir(), token + ext)
    shutil.move(path, target)
    try:
        summary = _summarise(target, source)
    except Exception:
        os.remove(target)
        raise
    with open(target, "rb") as f:
        sha = hashlib.file_digest(f, "sha256").hexdigest()
    summary.update(token=token, ext=ext, created=time.time(), sha=sha, kind=kind)
    with open(os.path.join(uploads_dir(), token + ".json"), "w", encoding="utf-8") as f:
        json.dump(summary, f)
    return summary


def from_upload(filename, stream):
    ext = os.path.splitext(filename or "")[1].lower()
    if ext not in EXTENSIONS:
        raise InputError("Upload a .pdb or .cif (mmCIF) file.")
    limit = int(settings.MAX_UPLOAD_MB * 1024 * 1024)
    tmp = os.path.join(uploads_dir(), "incoming-" + secrets.token_hex(8) + ext)
    size = 0
    with open(tmp, "wb") as f:
        while chunk := stream.read(1 << 20):
            size += len(chunk)
            if size > limit:
                f.close()
                os.remove(tmp)
                raise InputError(f"Files up to {settings.MAX_UPLOAD_MB:g} MB are accepted.")
            f.write(chunk)
    return _store(tmp, ".pdb" if ext == ".ent" else ext, os.path.basename(filename), "upload")


def from_pdb_id(pdb_id):
    pdb_id = (pdb_id or "").strip()
    if not PDB_ID.match(pdb_id):
        raise InputError("A PDB id is 4 characters, starting with a digit (e.g. 1EMA).")
    pdb_id = pdb_id.upper()
    stored = library.find_source(pdb_id)
    if stored is not None and os.path.exists(library.path_of(stored)):
        return _copy_in(library.path_of(stored), stored["ext"], pdb_id, "rcsb")
    limit = int(settings.MAX_UPLOAD_MB * 4 * 1024 * 1024)   # mmCIF text is larger than the PDB format
    tmp = os.path.join(uploads_dir(), "incoming-" + secrets.token_hex(8) + ".cif")
    try:
        with httpx.stream("GET", settings.RCSB_DOWNLOAD.format(id=pdb_id), timeout=60,
                          follow_redirects=True) as response:
            if response.status_code == 404:
                raise InputError(f"RCSB has no entry {pdb_id}.")
            response.raise_for_status()
            size = 0
            with open(tmp, "wb") as f:
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > limit:
                        raise InputError(f"{pdb_id} is too large to build here.")
                    f.write(chunk)
    except InputError:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    except httpx.HTTPError as e:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise InputError("Could not download from RCSB; try again later.") from e
    return _store(tmp, ".cif", pdb_id, "rcsb")


def _copy_in(path, ext, source, kind):
    tmp = os.path.join(uploads_dir(), "incoming-" + secrets.token_hex(8) + ext)
    shutil.copyfile(path, tmp)
    return _store(tmp, ext, source, kind)


def from_preset(name):
    if name not in presets():
        raise InputError("Unknown preset.")
    return _copy_in(os.path.join(resources.presets_dir(), name + ".pdb"), ".pdb", name, "preset")


def from_library(key):
    entry = library.get(key or "")
    if entry is None or not os.path.exists(library.path_of(entry)):
        raise InputError("That saved structure is no longer available.")
    return _copy_in(library.path_of(entry), entry["ext"], entry["source"], "saved")


def get(token):
    """Summary of an earlier upload, including its 'path'."""
    if not TOKEN.match(token or ""):
        raise InputError("Unknown structure; choose it again.")
    meta = os.path.join(uploads_dir(), token + ".json")
    if not os.path.exists(meta):
        raise InputError("This structure has expired; choose it again.")
    with open(meta, encoding="utf-8") as f:
        summary = json.load(f)
    summary["path"] = os.path.join(uploads_dir(), token + summary["ext"])
    return summary


def clean_uploads(max_age_hours=6):
    cutoff = time.time() - max_age_hours * 3600
    for name in os.listdir(uploads_dir()):
        path = os.path.join(uploads_dir(), name)
        if os.path.getmtime(path) < cutoff:
            os.remove(path)
