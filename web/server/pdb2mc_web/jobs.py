"""
Build queue: one build at a time. PDB2MC runs in a child process (so a build that takes too long can be
stopped); the result is then placed on a free plot. Expired plots are cleared by the same worker, so
builds and clean-ups never touch the world at the same time.
"""
import collections
import logging
import multiprocessing
import os
import queue
import shutil
import threading
import time
import uuid

from PDB2MC import defaults

from . import inputs, library, settings
from .world import cells_bounds, cells_needed, center, find_cells, map_link, plot_bounds

log = logging.getLogger(__name__)

# Options a visitor may set, with their types; everything else comes from the mode's defaults
OPTIONS = {"by_chain": bool, "show_hetatm": bool, "mesh": bool, "backbone": bool, "sidechain": bool,
           "bar_style": bool}
MODE_OPTIONS = {
    "Skeleton": ["by_chain", "backbone", "sidechain", "show_hetatm"],
    "Custom": ["by_chain", "backbone", "sidechain", "show_hetatm", "mesh"],
    "X-Ray": ["by_chain", "backbone", "sidechain", "show_hetatm", "mesh"],
    "Space Filling": ["by_chain", "show_hetatm", "mesh"],
    "Ribbon": ["by_chain", "bar_style", "show_hetatm"],
    "Amino Acids": ["backbone", "show_hetatm"],
}


def _build_child(mode, config, messages):
    try:
        from PDB2MC import build
        name = build.build_model(mode, config, progress=lambda value: messages.put(("progress", value)))
        messages.put(("done", name))
    except Exception as e:
        messages.put(("error", f"{type(e).__name__}: {e}"))


def model_fingerprint(sha, mode, scale, options):
    """Identifies a model: the same structure file built the same way gives the same model."""
    return f"{sha}|{mode}|{float(scale):.1f}|" + ",".join(f"{k}={int(v)}" for k, v in sorted(options.items()))


def public_plot(number, plot):
    bounds = plot_bounds(number, plot)
    return {"number": number, "title": plot["title"], "mode": plot["mode"], "scale": plot["scale"],
            "created": plot["created"], "expires": plot["expires"], "blocks": plot["blocks"],
            "center": list(center(bounds)), "size": bounds[2] - bounds[0] + 1,
            "command": f"/trigger plot set {number}", "map_url": map_link(bounds)}


class Job:
    def __init__(self, token, mode, scale, options, client):
        self.id = uuid.uuid4().hex
        self.token, self.mode, self.scale, self.options, self.client = token, mode, scale, options, client
        self.status = "queued"
        self.progress = 0
        self.message = "Waiting for earlier builds"
        self.plot = None
        self.existing = False
        self.created = time.time()

    def public(self, position=None):
        return {"id": self.id, "status": self.status, "progress": self.progress, "message": self.message,
                "position": position, "plot": self.plot, "existing": self.existing}


class Builder:
    def __init__(self, world, store, process_context=None):
        self.world, self.store = world, store
        self._ctx = process_context or multiprocessing.get_context("spawn")
        self._queue = queue.Queue()
        self._jobs = collections.OrderedDict()
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._thread = None
        self.last_error = None

    # --- public ---
    def start(self):
        self._thread = threading.Thread(target=self._run, name="builder", daemon=True)
        self._thread.start()

    @property
    def ready(self):
        return self._ready.is_set()

    def submit(self, token, mode, scale, options, client):
        if mode not in defaults.MODES:
            raise inputs.InputError("Unknown mode.")
        summary = inputs.get(token)
        try:
            scale = float(scale)
        except (TypeError, ValueError):
            raise inputs.InputError("Scale must be a number.")
        if not 1 <= scale <= summary["max_scale"]:
            raise inputs.InputError(f"Scale must be between 1 and {summary['max_scale']:g} for this structure.")
        # Every option of the mode, with the mode's default for those not given, so identical requests
        # get identical fingerprints
        defaults_of_mode = defaults.default_config(mode)
        options = options or {}
        options = {k: OPTIONS[k](options.get(k, defaults_of_mode[k])) for k in MODE_OPTIONS[mode]}
        scale = round(scale, 1)
        with self._lock:
            if any(j.client == client and j.status in ("queued", "building", "placing")
                   for j in self._jobs.values()):
                raise inputs.InputError("You already have a build in progress.")
            job = Job(token, mode, scale, options, client)
            self._jobs[job.id] = job
            while len(self._jobs) > 500:
                self._jobs.popitem(last=False)
        self._queue.put(job.id)
        return job

    def status(self, job_id):
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return None
            waiting = [j.id for j in self._jobs.values() if j.status == "queued"]
        position = waiting.index(job_id) + 1 if job_id in waiting else None
        return job.public(position)

    def plots(self):
        return [public_plot(n, p) for n, p in sorted(self.store.plots().items())]

    # --- worker ---
    def _run(self):
        while True:
            try:
                self._prepare_world()
                break
            except Exception as e:
                self.last_error = f"Minecraft server not reachable: {e}"
                log.warning(self.last_error)
                time.sleep(15)
        self._ready.set()
        self.last_error = None
        next_cleanup = 0
        while True:
            if time.time() >= next_cleanup:
                self._cleanup()
                next_cleanup = time.time() + 60
            try:
                job_id = self._queue.get(timeout=5)
            except queue.Empty:
                continue
            with self._lock:
                job = self._jobs.get(job_id)
            if job is not None:
                self._process(job)

    def _prepare_world(self):
        self.world.setup(self.store.plots())

    def _cleanup(self):
        changed = False
        for number, plot in self.store.expired().items():
            try:
                self.world.clear(plot_bounds(number, plot), plot["name"], plot["origin"])
                self._delete_input(plot["name"])
                self.store.remove(number)
                changed = True
                log.info("cleared plot %s (%s)", number, plot["name"])
            except Exception:
                log.exception("clearing plot %s failed; will retry", number)
        if changed:
            self.world.write_plot_pack(self.store.plots())
            self.world.reload()
        try:
            inputs.clean_uploads()
        except OSError:
            log.exception("cleaning uploads failed")

    def _models_dir(self):
        path = os.path.join(settings.STATE_DIR, "models")
        os.makedirs(path, exist_ok=True)
        return path

    def _delete_input(self, name):
        for f in os.listdir(self._models_dir()):
            if os.path.splitext(f)[0] == name:
                os.remove(os.path.join(self._models_dir(), f))

    def _set(self, job, status=None, message=None, progress=None):
        with self._lock:
            if status is not None:
                job.status = status
            if message is not None:
                job.message = message
            if progress is not None:
                job.progress = progress

    def _fail(self, job, message, name=None):
        self._set(job, status="error", message=message)
        if name:
            self.world.delete_model(name)
            self._delete_input(name)

    def _process(self, job):
        try:
            summary = inputs.get(job.token)
        except inputs.InputError as e:
            return self._fail(job, str(e))
        fingerprint = model_fingerprint(summary["sha"], job.mode, job.scale, job.options)
        found = self.store.find(fingerprint)
        if found is not None:
            # The same model is already in the world: send the visitor there and restart its timer
            number, _ = found
            plot = self.store.extend(number, time.time() + settings.PLOT_HOURS * 3600)
            library.touch(summary["sha"])
            with self._lock:
                job.plot = public_plot(number, plot)
                job.existing = True
            return self._set(job, status="done", progress=100,
                             message="This model is already in the world; its timer has been restarted")
        number = self.store.free_plot()
        if number is None:
            return self._fail(job, "Every plot is in use right now. Plots free up after "
                                   f"{settings.PLOT_HOURS:g} hours; please try again later.")
        name = self.store.new_model_name()
        source = os.path.join(self._models_dir(), name + summary["ext"])
        shutil.copyfile(summary["path"], source)
        config = defaults.default_config(job.mode)
        config.update(job.options, scale=job.scale, pdb_file=source, save_path=self.world.functions_dir)

        self._set(job, status="building", message="Building the model", progress=1)
        error = self._build(job, config)
        if error:
            return self._fail(job, error, name)
        try:
            low, high, blocks = self.world.model_extent(name)
        except Exception as e:
            return self._fail(job, f"The build produced no model ({e}).", name)
        if blocks > settings.MAX_BLOCKS:
            return self._fail(job, f"This model has {blocks:,} blocks; the limit is {settings.MAX_BLOCKS:,}. "
                                   "Try a smaller scale or the mesh option.", name)
        width = max(high[0] - low[0], high[2] - low[2]) + 1
        size = cells_needed(width)
        if size > settings.MAX_PLOT_CELLS or settings.GROUND_Y - low[1] + high[1] > settings.TOP_Y:
            return self._fail(job, "At this scale the model is larger than the largest plot; try a smaller scale.",
                              name)
        # the plot is sized to the model: the smallest free block of size x size cells
        number = self.store.free_plot()
        cells = find_cells(self.store.plots(), size)
        if number is None or cells is None:
            return self._fail(job, "There is no room for a model this large right now. Plots free up after "
                                   f"{settings.PLOT_HOURS:g} hours; please try again later or use a smaller scale.",
                              name)
        bounds = cells_bounds(*cells, size)
        origin = self.world.origin_for(bounds, low, high)

        self._set(job, status="placing", message="Placing it in the world", progress=90)
        now = time.time()
        plot = {"name": name, "title": summary["title"], "mode": job.mode, "scale": job.scale,
                "sha": summary["sha"], "fingerprint": fingerprint, "options": job.options,
                "origin": list(origin), "cells": [*cells, size], "blocks": blocks, "created": now,
                "expires": now + settings.PLOT_HOURS * 3600}
        try:
            self.store.add(number, plot)
            self.world.write_plot_pack(self.store.plots())
            self.world.place(bounds, name, origin)
        except Exception as e:
            log.exception("placing %s on plot %s failed", name, number)
            self.store.remove(number)
            try:
                self.world.clear(bounds, name, origin)
            except Exception:
                log.exception("removing the partly placed %s failed", name)
                # keep it registered as expired, so the clean-up retries
                self.store.add(number, dict(plot, expires=0))
            return self._set(job, status="error", message=f"Placing the model failed: {e}")
        try:
            # Examples ship with PDB2MC, so only visitors' own structures are kept
            if summary.get("kind") != "preset":
                library.add(summary, source)
        except OSError:
            log.exception("keeping %s in the library failed", name)
        with self._lock:
            job.plot = public_plot(number, plot)
        self._set(job, status="done", message="Ready", progress=100)

    def _build(self, job, config):
        """Run PDB2MC; returns an error message, or None when the build succeeded."""
        messages = self._ctx.Queue()
        process = self._ctx.Process(target=_build_child, args=(job.mode, config, messages), daemon=True)
        process.start()
        deadline = time.time() + settings.BUILD_TIMEOUT
        try:
            while time.time() < deadline:
                try:
                    kind, value = messages.get(timeout=1)
                except queue.Empty:
                    if not process.is_alive():
                        return "The build stopped unexpectedly."
                    continue
                if kind == "progress":
                    self._set(job, progress=max(1, int(value * 0.85)))
                elif kind == "done":
                    return None
                else:
                    log.warning("build failed: %s", value)
                    return f"The build failed: {value}"
            return (f"The build took longer than {settings.BUILD_TIMEOUT} seconds. "
                    "Try a smaller scale or a simpler mode.")
        finally:
            if process.is_alive():
                process.terminate()
            process.join(5)
