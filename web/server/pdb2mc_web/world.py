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


def plot_center(number):
    """Centre (x, z) of plot `number` (1-based); plots are laid out in rows east of spawn."""
    col, row = (number - 1) % settings.PLOTS_PER_ROW, (number - 1) // settings.PLOTS_PER_ROW
    return settings.PLOT_PITCH * (col + 1), settings.PLOT_PITCH * row


def plot_bounds(number):
    """(x1, z1, x2, z2) of the buildable area of a plot, inclusive."""
    cx, cz = plot_center(number)
    half = settings.PLOT_SIZE // 2
    return cx - half, cz - half, cx + half - 1, cz + half - 1


def teleport_target(number):
    """Where /trigger plot puts a player: just outside the plot's south edge, facing its centre."""
    cx, cz = plot_center(number)
    return cx, settings.GROUND_Y + 2, cz + settings.PLOT_SIZE // 2 + 6


def map_link(number):
    cx, cz = plot_center(number)
    return f"{settings.MAP_URL}/#world:{cx}:{settings.GROUND_Y + 40}:{cz}:260:0:0.9:0:0:perspective"


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
            x, y, z = teleport_target(number)
            cx, cz = plot_center(number)
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

    def origin_for(self, number, low, high):
        """Execution position that centres a model of extent low..high on plot `number`, on the ground."""
        cx, cz = plot_center(number)
        return (cx - (low[0] + high[0]) // 2, settings.GROUND_Y - low[1], cz - (low[2] + high[2]) // 2)

    def delete_model(self, name):
        mcf.delete_old_files(self.functions_dir, name)

    # --- placing ---
    def _wait_loaded(self, number, timeout=60):
        x1, z1, x2, z2 = plot_bounds(number)
        corners = [(x1, z1), (x2, z2), (x1, z2), (x2, z1)]
        deadline = time.time() + timeout
        while time.time() < deadline:
            if all("passed" in self.run(f"execute if loaded {x} {settings.GROUND_Y} {z}").lower()
                   for x, z in corners):
                return
            time.sleep(0.5)
        raise RuntimeError("The plot's chunks did not load in time.")

    def _with_plot_loaded(self, number, action):
        x1, z1, x2, z2 = plot_bounds(number)
        self.run(f"forceload add {x1} {z1} {x2} {z2}")
        try:
            self._wait_loaded(number)
            return action()
        finally:
            self.run("save-all")
            self.run(f"forceload remove {x1} {z1} {x2} {z2}")

    def _run_function(self, name, origin):
        x, y, z = origin
        output = self.run(f"execute positioned {x} {y} {z} run function protein:{name}")
        if "unknown" in output.lower() or "can't find" in output.lower():
            raise RuntimeError(f"Minecraft did not find function {name}: {output}")
        return output

    def place(self, number, name, origin):
        self.reload()
        self._with_plot_loaded(number, lambda: self._run_function(f"build_{name}", origin))
        self.run("bluemap update world")

    def clear(self, number, name, origin):
        """
        Remove a model's blocks from its plot, then its files. If removing the blocks fails the files
        are kept (the clear function needs them) and the error is raised, so the caller retries later.
        """
        self._with_plot_loaded(number, lambda: self._run_function(f"clear_{name}", origin))
        self.delete_model(name)
        self.run("bluemap update world")
