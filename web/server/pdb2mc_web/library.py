"""
Structures that have been built, kept so later visitors can pick them again: <state>/library/<id><ext>,
indexed in <state>/library/library.json. A file is stored once, keyed by its content (SHA-256); when the
library grows past LIBRARY_MAX_MB, the structures built longest ago are dropped.
"""
import json
import os
import shutil
import threading
import time

from . import settings

_lock = threading.Lock()


def _dir():
    path = os.path.join(settings.STATE_DIR, "library")
    os.makedirs(path, exist_ok=True)
    return path


def _index_path():
    return os.path.join(_dir(), "library.json")


def _load():
    if os.path.exists(_index_path()):
        with open(_index_path(), encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(index):
    tmp = _index_path() + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=1)
    os.replace(tmp, _index_path())


def entry_id(sha):
    return sha[:20]


def path_of(entry):
    return os.path.join(_dir(), entry["id"] + entry["ext"])


def add(summary, path):
    """Keep the structure of a successful build (summary from inputs, path of its file)."""
    with _lock:
        index = _load()
        key = entry_id(summary["sha"])
        entry = index.get(key)
        if entry is None:
            entry = {k: summary[k] for k in ("title", "source", "atoms", "chains", "ext")}
            entry.update(id=key, sha=summary["sha"], added=time.time(), builds=0,
                         size=os.path.getsize(path))
            shutil.copyfile(path, path_of(entry))
            index[key] = entry
        entry["builds"] += 1
        entry["last_built"] = time.time()
        _evict(index)
        _save(index)
        return dict(entry)


def touch(sha):
    """Count another build of a stored structure (a duplicate model that was reused)."""
    with _lock:
        index = _load()
        entry = index.get(entry_id(sha))
        if entry is not None:
            entry["builds"] += 1
            entry["last_built"] = time.time()
            _save(index)


def _evict(index):
    limit = settings.LIBRARY_MAX_MB * 1024 * 1024
    total = sum(e["size"] for e in index.values())
    for entry in sorted(index.values(), key=lambda e: e["last_built"]):
        if total <= limit:
            break
        total -= entry["size"]
        if os.path.exists(path_of(entry)):
            os.remove(path_of(entry))
        del index[entry["id"]]


def get(key):
    with _lock:
        return _load().get(key)


def find_source(source):
    """The stored structure downloaded as `source` (an RCSB id), if any."""
    with _lock:
        return next((e for e in _load().values() if e["source"].upper() == source.upper()), None)


def entries(query="", limit=200):
    """Stored structures, most recently built first, optionally filtered by title or source."""
    query = (query or "").strip().lower()
    with _lock:
        found = [e for e in _load().values()
                 if not query or query in e["title"].lower() or query in e["source"].lower()]
    found.sort(key=lambda e: e["last_built"], reverse=True)
    return [{k: e[k] for k in ("id", "title", "source", "atoms", "chains", "builds", "last_built")}
            for e in found[:limit]]
