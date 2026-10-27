"""Plots and the model counter, saved in <state>/plots.json."""
import json
import os
import threading
import time

from . import settings


class PlotStore:
    def __init__(self, state_dir=None):
        self.path = os.path.join(state_dir or settings.STATE_DIR, "plots.json")
        self._lock = threading.Lock()
        self._data = {"next_model": 1, "plots": {}}
        if os.path.exists(self.path):
            with open(self.path, encoding="utf-8") as f:
                self._data.update(json.load(f))

    def _save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=1)
        os.replace(tmp, self.path)

    def plots(self):
        """{number: plot dict} of every occupied plot."""
        with self._lock:
            return {int(n): dict(p) for n, p in self._data["plots"].items()}

    def new_model_name(self):
        with self._lock:
            number = self._data["next_model"]
            self._data["next_model"] = number + 1
            self._save()
            return f"m{number:06d}"

    def free_plot(self):
        """Lowest free plot number, or None when every plot is taken."""
        with self._lock:
            taken = {int(n) for n in self._data["plots"]}
        return next((n for n in range(1, settings.MAX_PLOTS + 1) if n not in taken), None)

    def add(self, number, plot):
        with self._lock:
            self._data["plots"][str(number)] = plot
            self._save()

    def remove(self, number):
        with self._lock:
            self._data["plots"].pop(str(number), None)
            self._save()

    def find(self, fingerprint):
        """(number, plot) of the plot holding an identical model, or None."""
        return next(((n, p) for n, p in self.plots().items() if p.get("fingerprint") == fingerprint), None)

    def extend(self, number, expires):
        with self._lock:
            plot = self._data["plots"].get(str(number))
            if plot is not None:
                plot["expires"] = max(plot["expires"], expires)
                self._save()
                return dict(plot)

    def expired(self, now=None):
        now = time.time() if now is None else now
        return {n: p for n, p in self.plots().items() if p["expires"] <= now}
