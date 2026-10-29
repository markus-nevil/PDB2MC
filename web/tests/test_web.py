import os
import socket
import struct
import sys
import threading
import time

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "server"))
sys.path.insert(0, os.path.join(HERE, "..", ".."))

from fastapi.testclient import TestClient  # noqa: E402

from pdb2mc_web import inputs, settings  # noqa: E402
from pdb2mc_web.app import create_app  # noqa: E402
from pdb2mc_web.jobs import Builder  # noqa: E402
from pdb2mc_web.rcon import Rcon  # noqa: E402
from pdb2mc_web.store import PlotStore  # noqa: E402
from pdb2mc_web.world import (World, cells_bounds, cells_needed, center, chunk_batches,  # noqa: E402
                               find_cells, max_plot_width, plot_bounds)


class FakeConsole:
    """Stands in for the RCON connection; records commands."""

    def __init__(self):
        self.commands = []

    def command(self, text):
        self.commands.append(text)
        if text.startswith("execute if loaded"):
            return "Test passed"
        if " run function " in text:
            return f"Running function {text.rsplit(' ', 1)[1]}"
        return ""


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STATE_DIR", str(tmp_path / "state"))
    monkeypatch.setattr(settings, "WORLD_DIR", str(tmp_path / "data" / "world"))
    os.makedirs(settings.STATE_DIR)
    console = FakeConsole()
    world = World(console)
    builder = Builder(world, PlotStore())
    builder._prepare_world()
    builder._ready.set()
    return builder, world, console


def build_now(builder, token, mode="Skeleton", scale=1.0, options=None, client="1.2.3.4"):
    job = builder.submit(token, mode, scale, options or {}, client)
    builder._queue.get_nowait()
    builder._process(job)
    return builder.status(job.id)


def test_plot_layout():
    x1, z1, x2, z2 = plot_bounds(1, {})
    assert x2 - x1 + 1 == settings.PLOT_SIZE == z2 - z1 + 1
    assert x1 % 16 == 0 and z1 % 16 == 0      # whole chunks
    # plots made before plots could grow keep their place
    assert center(plot_bounds(1, {})) == (settings.PLOT_PITCH, 0)
    assert center(plot_bounds(settings.PLOTS_PER_ROW + 1, {})) == (settings.PLOT_PITCH, settings.PLOT_PITCH)
    assert plot_bounds(3, {"cells": [2, 0, 1]}) == plot_bounds(3, {})


def test_plots_grow_with_the_model():
    assert cells_needed(1) == cells_needed(settings.PLOT_SIZE) == 1
    assert cells_needed(settings.PLOT_SIZE + 1) == 2
    assert cells_needed(max_plot_width()) == settings.MAX_PLOT_CELLS
    x1, z1, x2, z2 = cells_bounds(1, 2, 3)
    assert x2 - x1 + 1 == 3 * settings.PLOT_PITCH - (settings.PLOT_PITCH - settings.PLOT_SIZE)
    # a 2 x 2 plot skips cells that are taken
    plots = {1: {"cells": [0, 0, 1]}, 2: {"cells": [3, 0, 1]}}
    assert find_cells(plots, 1) == (1, 0)
    assert find_cells(plots, 2) == (1, 0)
    assert find_cells({1: {"cells": [1, 0, 1]}}, 2) == (2, 0)
    full_row = {1: {"cells": [0, 0, 4]}, 2: {"cells": [4, 0, 4]}}
    assert find_cells(full_row, 4) == (0, 4)
    assert find_cells(full_row, settings.PLOT_ROWS) is None                   # larger than the grid
    # forceload covers at most 16 x 16 chunks per command; the batches cover the plot exactly
    bounds = cells_bounds(0, 0, 4)
    batches = list(chunk_batches(bounds))
    assert len(batches) > 1
    assert all(((b[2] - b[0] + 1) // 16) * ((b[3] - b[1] + 1) // 16) <= 256 for b in batches)
    assert sum((b[2] - b[0] + 1) * (b[3] - b[1] + 1) for b in batches) == (
        (bounds[2] - bounds[0] + 1) * (bounds[3] - bounds[1] + 1))


def test_scale_limit_comes_from_height_for_large_models():
    from PDB2MC import pdb_manipulation as pdbm
    structure = pdbm.load_structure(os.path.join(HERE, "..", "..", "UI", "presets", "Nucleosome.pdb"))
    # the Nucleosome is limited by the world height (about 4x), not by a single plot cell (about 2x)
    assert inputs.max_scale(structure) >= 4.0


def test_large_model_gets_a_larger_plot(env):
    builder, world, console = env
    build_now(builder, inputs.from_preset("ATP")["token"], client="a")          # takes cell (0, 0)
    status = build_now(builder, inputs.from_preset("Hemoglobin")["token"], scale=5.0, client="b")
    assert status["status"] == "done", status["message"]
    plot = builder.store.plots()[status["plot"]["number"]]
    assert plot["cells"][2] >= 2 and plot["cells"][:2] == [1, 0]
    assert status["plot"]["size"] == plot_bounds(0, plot)[2] - plot_bounds(0, plot)[0] + 1
    bounds = plot_bounds(0, plot)
    low, high, _ = world.model_extent(plot["name"])
    x, y, z = plot["origin"]
    assert bounds[0] <= x + low[0] and x + high[0] <= bounds[2] and bounds[1] <= z + low[2] and z + high[2] <= bounds[3]
    forceloads = [c for c in console.commands if c.startswith("forceload add")]
    assert len(forceloads) >= 2                                               # loaded in batches


def test_setup_writes_plot_pack_and_rules(env):
    builder, world, console = env
    pack = os.path.join(world.pack_dir, "data")
    for folder in ("function", "functions"):
        assert os.path.exists(os.path.join(pack, "plots", folder, "goto.mcfunction"))
        assert os.path.exists(os.path.join(pack, "minecraft", "tags", folder, "tick.json"))
    assert "minecraft:reload" in console.commands
    assert "reload" not in console.commands            # Paper's /reload would reload plugins
    assert any(c.startswith("gamerule spawn_mobs") for c in console.commands)


def test_preset_build_is_placed_and_expires(env):
    builder, world, console = env
    summary = inputs.from_preset("Helix")
    assert summary["max_scale"] >= summary["suggested_scale"] >= 1
    status = build_now(builder, summary["token"], scale=2.0, options={"by_chain": True, "evil": "x"})
    assert status["status"] == "done", status["message"]
    plot = status["plot"]
    assert plot["number"] == 1 and plot["command"] == "/trigger plot set 1"
    stored = builder.store.plots()[1]
    assert stored["name"] == "m000001"
    x, y, z = stored["origin"]
    assert f"execute positioned {x} {y} {z} run function protein:build_m000001" in console.commands
    # loaded before placing, released afterwards
    x1, z1, x2, z2 = plot_bounds(1, stored)
    assert console.commands.index(f"forceload add {x1} {z1} {x2} {z2}") < console.commands.index(
        f"execute positioned {x} {y} {z} run function protein:build_m000001") < console.commands.index(
        f"forceload remove {x1} {z1} {x2} {z2}")
    # the model sits on the plot, on the ground, under the height limit
    low, high, blocks = world.model_extent("m000001")
    assert blocks == stored["blocks"] > 0
    assert y + low[1] == settings.GROUND_Y and y + high[1] <= settings.TOP_Y
    assert x1 <= x + low[0] and x + high[0] <= x2 and z1 <= z + low[2] and z + high[2] <= z2
    goto = open(os.path.join(world.pack_dir, "data", "plots", "function", "goto.mcfunction")).read()
    assert "matches 1 run tp @s" in goto

    builder.store.add(1, dict(stored, expires=0))
    builder._cleanup()
    assert builder.store.plots() == {}
    assert f"execute positioned {x} {y} {z} run function protein:clear_m000001" in console.commands
    assert f"setblock {x} {y - 1} {z} minecraft:white_concrete" in console.commands  # obsidian marker removed
    assert world.model_files("m000001") == []
    assert "matches 1 run tp" not in open(os.path.join(world.pack_dir, "data", "plots", "function",
                                                       "goto.mcfunction")).read()


def test_failed_clear_keeps_files_for_retry(env):
    builder, world, console = env
    status = build_now(builder, inputs.from_preset("ATP")["token"])
    assert status["status"] == "done"
    stored = builder.store.plots()[1]
    builder.store.add(1, dict(stored, expires=0))
    console.command = lambda text: (_ for _ in ()).throw(OSError("server down"))
    builder._cleanup()
    assert 1 in builder.store.plots() and world.model_files(stored["name"])


def test_every_mode_builds(env):
    builder, world, console = env
    token = inputs.from_preset("Helix")["token"]
    for i, mode in enumerate(["Custom", "X-Ray", "Space Filling", "Ribbon", "Amino Acids"]):
        status = build_now(builder, token, mode=mode, client=f"10.0.0.{i}")
        assert status["status"] == "done", (mode, status["message"])
    assert sorted(builder.store.plots()) == [1, 2, 3, 4, 5]
    names = {p["name"] for p in builder.store.plots().values()}
    assert len(names) == 5                       # every build gets its own model name


def test_too_large_scale_and_full_world(env, monkeypatch):
    builder, world, console = env
    summary = inputs.from_preset("Helix")
    with pytest.raises(inputs.InputError):
        builder.submit(summary["token"], "Skeleton", summary["max_scale"] + 1, {}, "a")
    monkeypatch.setattr(settings, "MAX_PLOTS", 0)
    status = build_now(builder, summary["token"])
    assert status["status"] == "error" and "Every plot" in status["message"]


def test_build_timeout_is_reported(env, monkeypatch):
    builder, world, console = env
    monkeypatch.setattr(settings, "BUILD_TIMEOUT", 0)
    status = build_now(builder, inputs.from_preset("Helix")["token"])
    assert status["status"] == "error" and "longer than" in status["message"]
    assert os.listdir(os.path.join(settings.STATE_DIR, "models")) == []


def test_one_build_per_visitor(env):
    builder, world, console = env
    token = inputs.from_preset("Helix")["token"]
    builder.submit(token, "Skeleton", 1, {}, "same")
    with pytest.raises(inputs.InputError):
        builder.submit(token, "Skeleton", 1, {}, "same")


def test_input_validation(env, tmp_path):
    with pytest.raises(inputs.InputError):
        inputs.from_pdb_id("../etc")
    with pytest.raises(inputs.InputError):
        inputs.get("../../secret")
    with pytest.raises(inputs.InputError):
        inputs.from_upload("x.exe", open(__file__, "rb"))
    bad = tmp_path / "bad.pdb"
    bad.write_text("not a structure\n")
    with pytest.raises(inputs.InputError):
        inputs.from_upload("bad.pdb", open(bad, "rb"))


def test_api(env, monkeypatch):
    builder, world, console = env
    client = TestClient(create_app(builder))
    config = client.get("/api/config").json()
    assert {m["name"] for m in config["modes"]} >= {"Skeleton", "Space Filling"} and "GFP" in config["presets"]
    assert config["play_host"] == settings.PLAY_HOST and config["bedrock_port"] == 19132
    chosen = client.post("/api/structures", data={"preset": "Helix"}).json()
    with open(os.path.join(HERE, "..", "..", "UI", "presets", "ATP.pdb"), "rb") as f:
        uploaded = client.post("/api/structures", files={"file": ("atp.pdb", f)}).json()
    assert uploaded["atoms"] > 0 and uploaded["source"] == "atp.pdb"
    assert client.post("/api/structures", data={}).status_code == 400
    job = client.post("/api/builds", json={"token": chosen["token"], "mode": "Ribbon", "scale": 1}).json()
    assert job["status"] == "queued" and job["position"] == 1
    assert client.get(f"/api/builds/{job['id']}").json()["status"] == "queued"
    assert client.get("/api/builds/nope").status_code == 404
    # one build per hour: a second request from the same visitor is refused
    monkeypatch.setattr(settings, "BUILDS_PER_HOUR", 1)
    limited = TestClient(create_app(builder))
    body = {"token": chosen["token"], "mode": "Ribbon", "scale": 1}
    assert limited.post("/api/builds", json=body).status_code == 400       # already has a queued build
    assert limited.post("/api/builds", json=body).status_code == 429
    # behind the tunnel, visitors are told apart by CF-Connecting-IP, but only from the trusted proxy
    assert limited.post("/api/builds", json=body, headers={"cf-connecting-ip": "9.9.9.9"}).status_code == 429
    monkeypatch.setattr(settings, "TRUSTED_PROXIES", {"testclient"})
    for visitor in ("9.9.9.9", "8.8.8.8"):
        response = limited.post("/api/builds", json=body, headers={"cf-connecting-ip": visitor})
        assert response.status_code == 200, response.text


class FakeRconServer(threading.Thread):
    def __init__(self, password):
        super().__init__(daemon=True)
        self.password = password
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen()
        self.port = self.sock.getsockname()[1]

    def run(self):
        conn, _ = self.sock.accept()

        def read():
            size = struct.unpack("<i", conn.recv(4))[0]
            data = b""
            while len(data) < size:
                data += conn.recv(size - len(data))
            return struct.unpack("<ii", data[:8]) + (data[8:-2].decode(),)

        def send(request_id, kind, body):
            payload = struct.pack("<ii", request_id, kind) + body.encode() + b"\x00\x00"
            conn.sendall(struct.pack("<i", len(payload)) + payload)

        request_id, kind, body = read()
        send(request_id if body == self.password else -1, 2, "")
        while True:
            try:
                request_id, kind, body = read()
            except Exception:
                return
            send(request_id, 0, f"echo {body}")


def test_rcon_client():
    server = FakeRconServer("pw")
    server.start()
    rcon = Rcon("127.0.0.1", server.port, "pw", timeout=5)
    assert rcon.command("list") == "echo list"
    assert rcon.command("time set noon") == "echo time set noon"
    rcon.close()


def test_identical_model_reuses_plot_and_restarts_timer(env):
    builder, world, console = env
    first = build_now(builder, inputs.from_preset("Helix")["token"], options={"by_chain": False})
    assert first["status"] == "done" and not first["existing"]
    stored = builder.store.plots()[1]
    builder.store.add(1, dict(stored, expires=stored["expires"] - 3600))       # an hour has passed
    # the same file (uploaded under another name), same style and scale, defaults left out
    with open(os.path.join(HERE, "..", "..", "UI", "presets", "Helix.pdb"), "rb") as f:
        again = inputs.from_upload("my-helix.pdb", f)
    second = build_now(builder, again["token"], client="5.6.7.8")
    assert second["status"] == "done" and second["existing"] and second["plot"]["number"] == 1
    assert builder.store.plots()[1]["expires"] > stored["expires"] - 3600
    assert sorted(builder.store.plots()) == [1]
    assert len(world.model_files("m000002")) == 0                                # nothing was built
    from pdb2mc_web import library
    assert library.entries() == []                                               # examples are not kept
    # another style is a different model
    third = build_now(builder, again["token"], mode="Ribbon", client="9.9.9.9")
    assert third["status"] == "done" and not third["existing"] and third["plot"]["number"] == 2
    assert [e["source"] for e in library.entries()] == ["my-helix.pdb"]


def test_built_structures_are_kept_and_can_be_picked(env):
    from pdb2mc_web import library
    builder, world, console = env
    upload = os.path.join(HERE, "..", "..", "UI", "presets", "ATP.pdb")
    with open(upload, "rb") as f:
        chosen = inputs.from_upload("atp.pdb", f)
    assert library.entries() == []                     # only structures that were built are kept
    assert build_now(builder, chosen["token"])["status"] == "done"
    saved = library.entries()
    assert [e["source"] for e in saved] == ["atp.pdb"] and saved[0]["builds"] == 1
    assert library.entries("atp")[0]["id"] == saved[0]["id"] and library.entries("nothing") == []
    picked = inputs.from_library(saved[0]["id"])
    assert picked["sha"] == chosen["sha"] and picked["atoms"] == chosen["atoms"]
    with pytest.raises(inputs.InputError):
        inputs.from_library("missing")


def test_rcsb_id_in_library_is_not_downloaded_again(env, monkeypatch):
    from pdb2mc_web import library
    builder, world, console = env
    summary = inputs.from_preset("GFP")
    summary.update(source="1EMA", kind="rcsb")
    library.add(summary, summary.get("path") or inputs.get(summary["token"])["path"])
    monkeypatch.setattr(settings, "RCSB_DOWNLOAD", "http://127.0.0.1:9/{id}")    # would fail if used
    assert inputs.from_pdb_id("1ema")["sha"] == summary["sha"]


def test_library_drops_oldest_when_full(env, monkeypatch):
    from pdb2mc_web import library
    builder, world, console = env
    first = inputs.from_preset("Helix")
    library.add(first, inputs.get(first["token"])["path"])
    second = inputs.from_preset("ATP")
    monkeypatch.setattr(settings, "LIBRARY_MAX_MB", (os.path.getsize(inputs.get(second["token"])["path"]) + 1) / 2**20)
    library.add(second, inputs.get(second["token"])["path"])
    assert [e["source"] for e in library.entries()] == ["ATP"]
