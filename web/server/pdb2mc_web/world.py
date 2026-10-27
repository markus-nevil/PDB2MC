"""
The shared Minecraft world: plot layout, placing and clearing models over RCON, and the small `plots`
datapack that lets any player (Java or Bedrock, no operator rights) teleport with /trigger plot set <n>.

Models are built by PDB2MC into the world's mcPDB datapack as usual; a model's build_/clear_ functions
place its structures relative to the execution position, so placing a model on a plot is
`execute positioned <origin> run function protein:build_<name>` while the plot's chunks are loaded.
"""
import json
import logging
import os
import time

import numpy as np

from PDB2MC import cli, minecraft_functions as mcf
from PDB2MC.nbt_writer import read_positions

from . import settings

log = logging.getLogger(__name__)

# Gamerules for a calm display world: (names, value). Minecraft 26.x renamed the rules to snake_case
# (and turned doFireTick into a radius); the first name the server accepts is used
GAMERULES = [(("advance_time", "doDaylightCycle"), "false"), (("advance_weather", "doWeatherCycle"), "false"),
             (("spawn_mobs", "doMobSpawning"), "false"), (("mob_griefing", "mobGriefing"), "false"),
             (("spawn_phantoms", "doInsomnia"), "false"), (("spawn_patrols", "doPatrolSpawning"), "false"),
             (("spawn_wandering_traders", "doTraderSpawning"), "false"),
             (("show_advancement_messages", "announceAdvancements"), "false"),
             (("respawn_radius", "spawnRadius"), "0"),
             (("fire_spread_radius_around_player",), "0"), (("doFireTick",), "false")]


# Plots are square blocks of grid cells: a cell is PLOT_SIZE blocks wide with PLOT_PITCH - PLOT_SIZE blocks
# of space to the next one, PLOTS_PER_ROW cells to a row, east of spawn. A model takes the smallest k x k
# block of free cells it fits in (k up to MAX_PLOT_CELLS). A 1 x 1 plot covers one cell exactly.
GAP = settings.PLOT_PITCH - settings.PLOT_SIZE
GRID_X0 = settings.PLOT_PITCH - settings.PLOT_SIZE // 2
GRID_Z0 = -(settings.PLOT_SIZE // 2)


def cells_needed(width):
    """Side k of the k x k cells a model `width` blocks wide needs (may exceed MAX_PLOT_CELLS)."""
    return max(1, -(-(width + GAP) // settings.PLOT_PITCH))


def max_plot_width():
    return settings.MAX_PLOT_CELLS * settings.PLOT_PITCH - GAP


def cells_bounds(col, row, size):
    """(x1, z1, x2, z2), inclusive, of the size x size cells starting at (col, row)."""
    x1 = GRID_X0 + col * settings.PLOT_PITCH
    z1 = GRID_Z0 + row * settings.PLOT_PITCH
    span = size * settings.PLOT_PITCH - GAP
    return x1, z1, x1 + span - 1, z1 + span - 1


def plot_cells(number, plot):
    """(col, row, size) of a plot; plots made before plots could grow were one cell, by number."""
    if plot.get("cells"):
        return tuple(plot["cells"])
    return (number - 1) % settings.PLOTS_PER_ROW, (number - 1) // settings.PLOTS_PER_ROW, 1


def plot_bounds(number, plot):
    return cells_bounds(*plot_cells(number, plot))


def find_cells(plots, size):
    """(col, row) of the first free size x size block of cells, or None."""
    taken = set()
    for number, plot in plots.items():
        col, row, k = plot_cells(number, plot)
        taken |= {(col + i, row + j) for i in range(k) for j in range(k)}
    for row in range(settings.PLOT_ROWS - size + 1):
        for col in range(settings.PLOTS_PER_ROW - size + 1):
            if not any((col + i, row + j) in taken for i in range(size) for j in range(size)):
                return col, row
    return None


def center(bounds):
    x1, z1, x2, z2 = bounds
    return (x1 + x2 + 1) // 2, (z1 + z2 + 1) // 2


def teleport_target(bounds):
    """Where /trigger plot puts a player: just outside the plot's south edge, facing its centre."""
    cx, _ = center(bounds)
    return cx, settings.GROUND_Y + 2, bounds[3] + 6


def map_link(bounds):
    cx, cz = center(bounds)
    distance = 260 + (bounds[2] - bounds[0])
    return f"{settings.MAP_URL}/#world:{cx}:{settings.GROUND_Y + 40}:{cz}:{distance}:0:0.9:0:0:perspective"


def chunk_batches(bounds):
    """The bounds split into pieces of at most 16 x 16 chunks (the limit of one forceload command)."""
    x1, z1, x2, z2 = bounds
    for bx in range(x1 >> 4, (x2 >> 4) + 1, 16):
        for bz in range(z1 >> 4, (z2 >> 4) + 1, 16):
            yield bx * 16, bz * 16, min(bx + 15, x2 >> 4) * 16 + 15, min(bz + 15, z2 >> 4) * 16 + 15


def _write_both(base, dirs, filename, text):
    for d in dirs:
        os.makedirs(os.path.join(base, d), exist_ok=True)
        with open(os.path.join(base, d, filename), "w", encoding="utf-8") as f:
            f.write(text)


class World:
    def __init__(self, rcon, world_dir=None):
        self.rcon = rcon
        self.world_dir = world_dir or settings.WORLD_DIR
        self.functions_dir = cli.datapack_dir(self.world_dir)
        self.pack_dir = os.path.join(self.world_dir, "datapacks", "mcPDB")

    # --- console ---
    def run(self, command):
        output = self.rcon.command(command)
        log.debug("%s -> %s", command, output)
        return output

    def reload(self):
        # minecraft:reload reloads data packs; Paper's plain /reload would reload plugins instead
        self.run("minecraft:reload")

    # --- setup ---
    def write_plot_pack(self, plots):
        """The plots datapack functions (in the mcPDB pack, next to the models' functions)."""
        data = os.path.join(self.pack_dir, "data")
        plots_ns = os.path.join(data, "plots")
        _write_both(plots_ns, mcf.FUNCTION_DIRS, "load.mcfunction",
                    "scoreboard objectives add plot trigger\nscoreboard objectives add spawn trigger\n")
        _write_both(plots_ns, mcf.FUNCTION_DIRS, "tick.mcfunction",
                    "scoreboard players enable @a plot\nscoreboard players enable @a spawn\n"
                    "execute as @a[scores={plot=1..}] at @s run function plots:goto\n"
                    "execute as @a[scores={spawn=1..}] run function plots:spawn\n")
        _write_both(plots_ns, mcf.FUNCTION_DIRS, "spawn.mcfunction",
                    f"tp @s 0 {settings.GROUND_Y} 0\nscoreboard players set @s spawn 0\n")
        lines = ["tag @s add pdb2mc_miss\n"]
        for number, plot in sorted(plots.items()):
            bounds = plot_bounds(number, plot)
            x, y, z = teleport_target(bounds)
            cx, cz = center(bounds)
            title = json.dumps(f"Plot {number}: {plot.get('title') or plot['name']}")
            lines += [f"execute if score @s plot matches {number} run tp @s {x} {y} {z} facing {cx} {y + 25} {cz}\n",
                      f"execute if score @s plot matches {number} run tellraw @s {{\"text\":{title},\"color\":\"aqua\"}}\n",
                      f"execute if score @s plot matches {number} run tag @s remove pdb2mc_miss\n"]
        lines += ['tellraw @s[tag=pdb2mc_miss] {"text":"There is no model on that plot. Make one at '
                  'build.pdb2mc.com","color":"red"}\n',
                  "tag @s remove pdb2mc_miss\n", "scoreboard players set @s plot 0\n"]
        _write_both(plots_ns, mcf.FUNCTION_DIRS, "goto.mcfunction", "".join(lines))
        tags = os.path.join(data, "minecraft", "tags")
        for d in ("functions", "function"):
            os.makedirs(os.path.join(tags, d), exist_ok=True)
            for name in ("load", "tick"):
                with open(os.path.join(tags, d, f"{name}.json"), "w") as f:
                    json.dump({"values": [f"plots:{name}"]}, f)

    def setup(self, plots):
        """Prepare a running server: datapack, triggers and gamerules. Safe to repeat."""
        self.write_plot_pack(plots)
        self.run('datapack enable "file/mcPDB"')
        self.reload()
        self.run("function plots:load")
        for names, value in GAMERULES:
            for rule in names:
                output = self.run(f"gamerule {rule} {value}").lower()
                if "unknown" not in output and "incorrect" not in output:
                    break
            else:
                log.info("gamerule %s not known to this server version", "/".join(names))
        self.run("time set noon")
        self.run("weather clear")
        self.run(f"setworldspawn 0 {settings.GROUND_Y} 0")

    # --- models ---
    def model_files(self, name):
        directory = mcf.structure_dirs(self.functions_dir)[0]
        return [os.path.join(directory, f) for f in sorted(os.listdir(directory))
                if mcf._is_model_file(f, name, ".nbt")]

    def model_extent(self, name):
        """(minimum (x, y, z), maximum (x, y, z), block count) of a built model relative to its origin."""
        positions = [read_positions(path) for path in self.model_files(name)]
        positions = np.concatenate(positions) if positions else np.zeros((0, 3), dtype=int)
        if not len(positions):
            raise ValueError("The model has no blocks.")
        return positions.min(axis=0).tolist(), positions.max(axis=0).tolist(), len(positions)

    def origin_for(self, bounds, low, high):
        """Execution position that centres a model of extent low..high on a plot, on the ground."""
        cx, cz = center(bounds)
        return (cx - (low[0] + high[0]) // 2, settings.GROUND_Y - low[1], cz - (low[2] + high[2]) // 2)

    def delete_model(self, name):
        mcf.delete_old_files(self.functions_dir, name)

    # --- placing ---
    def _wait_loaded(self, bounds, timeout=120):
        corners = [(x, z) for x1, z1, x2, z2 in chunk_batches(bounds)
                   for x, z in ((x1, z1), (x2, z2), (x1, z2), (x2, z1))]
        deadline = time.time() + timeout
        while time.time() < deadline:
            if all("passed" in self.run(f"execute if loaded {x} {settings.GROUND_Y} {z}").lower()
                   for x, z in corners):
                return
            time.sleep(0.5)
        raise RuntimeError("The plot's chunks did not load in time.")

    def _with_plot_loaded(self, bounds, action):
        batches = list(chunk_batches(bounds))
        for x1, z1, x2, z2 in batches:
            self.run(f"forceload add {x1} {z1} {x2} {z2}")
        try:
            self._wait_loaded(bounds)
            return action()
        finally:
            self.run("save-all")
            for x1, z1, x2, z2 in batches:
                self.run(f"forceload remove {x1} {z1} {x2} {z2}")

    def _run_function(self, name, origin):
        x, y, z = origin
        output = self.run(f"execute positioned {x} {y} {z} run function protein:{name}")
        if "unknown" in output.lower() or "can't find" in output.lower():
            raise RuntimeError(f"Minecraft did not find function {name}: {output}")
        return output

    def place(self, bounds, name, origin):
        self.reload()
        self._with_plot_loaded(bounds, lambda: self._run_function(f"build_{name}", origin))
        self.run("bluemap update world")

    def clear(self, bounds, name, origin):
        """
        Remove a model's blocks from its plot, then its files. If removing the blocks fails the files
        are kept (the clear function needs them) and the error is raised, so the caller retries later.
        """
        def clear_blocks():
            self._run_function(f"clear_{name}", origin)
            # build_ functions put an obsidian marker under the origin; clear_ leaves it
            x, y, z = origin
            ground = settings.GROUND_BLOCK if y - 1 == settings.GROUND_Y - 1 else "air"
            self.run(f"setblock {x} {y - 1} {z} minecraft:{ground}")

        self._with_plot_loaded(bounds, clear_blocks)
        self.delete_model(name)
        self.run("bluemap update world")
