"""
In-game commands for a world's models, on top of the usual /function protein:build_<name>.

Any player can use /trigger, with no operator rights and without cheats, so a whole class can share a world:

    /trigger models                                  list the models in the world
    /trigger build set <number>    /trigger build_<name>     build a model where you stand
    /trigger delete set <number>   /trigger delete_<name>    delete the newest copy, wherever it is
    /trigger plot set <number>     /trigger plot_<name>      teleport to the newest copy
    /trigger spawn                                   teleport to the world spawn

/function protein:build_<name> and /function protein:clear_<name> keep working and share the same records,
so a model built one way can be deleted the other way. /function pdb2mc:list is the list as a function.

How it works: every build notes where it happened in Minecraft's own command storage (pdb2mc:models), one list
of copies per model. Deleting takes a copy from that list; building starts from the player's position. Both go
through one queue that force-loads the model's whole footprint, waits for it, places the structures and releases
the chunks. That wait matters: while chunks are loading `place template` fails, part by part, and chunks it finds
missing are loaded on the server's main thread, which on new terrain makes the whole game wait. A clear_ function
with no record to go on does what it always did and clears around the player, so models built before this
existed can still be removed from their obsidian block.

Everything is generated into the mcPDB datapack, in the pdb2mc function namespace, by sync(). Model numbers are
kept in pdb2mc_models.json in the datapack, so a model keeps its number when it is rebuilt.

Remembering and deleting use function macros, so they need Minecraft 1.20.2 or newer. On older versions those
functions simply don't load: /function protein:build_<name> and clear_<name> then build and clear on the spot marked by an obsidian block.
"""
import json
import os
import re
import shutil

import numpy as np

from PDB2MC import minecraft_functions as mcf
from PDB2MC.nbt_writer import read_positions

REGISTRY_FILE = "pdb2mc_models.json"
NAMESPACE = "pdb2mc"
# Objectives with the number of the model as their value
NUMBER_TRIGGERS = ("build", "delete", "plot")
# `place template` refuses to start unless the chunks within a structure's size are loaded, and the size in
# PDB2MC's files is at most 32 blocks
LOADED_REACH = 32
# The most blocks one forceload command should span: it can take 256 chunks, which is 16 x 16 at any alignment
FORCELOAD_SPAN = 240
# Ticks between looks at whether a model's chunks have loaded, and how many looks to give them
WAIT_TICKS = 2
WAIT_TRIES = 3000

_MODEL_NAME = re.compile(r"^[a-z0-9_.-]+$")


# --- where things go ---

def _pack_dir(mc_dir):
    data = os.path.dirname(os.path.dirname(os.path.normpath(mc_dir)))
    return os.path.dirname(data)


def _function_roots(mc_dir):
    """The function folders of the pdb2mc namespace (old and new Minecraft name them differently)."""
    data = os.path.join(_pack_dir(mc_dir), "data")
    return [os.path.join(data, NAMESPACE, folder) for folder in mcf.FUNCTION_DIRS]


def _write_function(mc_dir, path, text):
    for root in _function_roots(mc_dir):
        file_path = os.path.join(root, *path.split("/")) + ".mcfunction"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)


# --- registry ---

def _registry_path(mc_dir):
    return os.path.join(_pack_dir(mc_dir), REGISTRY_FILE)


def _load_registry(mc_dir):
    try:
        with open(_registry_path(mc_dir), "r", encoding="utf-8") as f:
            registry = json.load(f)
    except (OSError, ValueError):
        registry = {}
    if not isinstance(registry, dict) or not isinstance(registry.get("models"), dict):
        registry = {"models": {}}
    registry.setdefault("retired", [])
    return registry


def _save_registry(mc_dir, registry):
    with open(_registry_path(mc_dir), "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, sort_keys=True)


def models(mc_dir):
    """{name: {"number": n, "mode": ..., "scale": ...}} of the world's models."""
    return _load_registry(mc_dir)["models"]


def model_number(mc_dir, name):
    entry = models(mc_dir).get(name.lower())
    return entry["number"] if entry else None


def _world_models(mc_dir):
    """Names of the models with a clear_ function and delete structures in this world."""
    functions = mcf.function_dirs(mc_dir)[0]
    if not os.path.isdir(functions):
        return []
    names = []
    structures = mcf.structure_dirs(mc_dir, create=False)[0]
    for filename in sorted(os.listdir(functions)):
        if filename.startswith("clear_") and filename.endswith(".mcfunction"):
            name = filename[len("clear_"):-len(".mcfunction")]
            if _MODEL_NAME.match(name) and os.path.isdir(structures) and len(mcf.find_delete_nbt(structures, name)):
                names.append(name)
    return names


def _next_number(taken):
    number = 1
    while number in taken:
        number += 1
    return number


# --- functions of one model ---

def _own_parts(frame, name, names):
    """Rows of a find_nbt / find_delete_nbt frame without the parts of a longer model such as <name>_2."""
    prefix = "delete_" if len(frame) and str(frame['group'].iloc[0]).startswith("delete_") else ""
    others = [f"{prefix}{other}_" for other in names if other != name and other.startswith(name + "_")]
    return frame[[not any(str(group).startswith(other) for other in others) for group in frame['group']]]


def _model_extent(mc_dir, parts):
    """(x1, z1, x2, z2) of a model around its origin, with the blocks `place template` wants loaded to start."""
    structures = mcf.structure_dirs(mc_dir)[0]
    positions = [read_positions(os.path.join(structures, f"{part}.nbt")) for part in parts['group']]
    positions = np.concatenate(positions) if positions else np.zeros((0, 3), dtype=int)
    if not len(positions):
        return [0, 0, LOADED_REACH, LOADED_REACH]
    low, high = positions.min(axis=0), positions.max(axis=0)
    return [min(0, int(low[0])), min(0, int(low[2])),
            max(LOADED_REACH, int(high[0])), max(LOADED_REACH, int(high[2]))]


def _forceload_lines(action, extent):
    """Commands that force-load or release a whole model, run at its origin."""
    x1, z1, x2, z2 = extent
    return "".join(f"forceload {action} ~{x} ~{z} ~{min(x + FORCELOAD_SPAN - 1, x2)} ~{min(z + FORCELOAD_SPAN - 1, z2)}\n"
                   for x in range(x1, x2 + 1, FORCELOAD_SPAN) for z in range(z1, z2 + 1, FORCELOAD_SPAN))


def _chunks_loaded_text(extent):
    """Clears #ready if a chunk of the model is not loaded yet; run at its origin."""
    x1, z1, x2, z2 = extent
    return "".join(f"execute unless loaded ~{x} ~ ~{z} run scoreboard players set #ready {NAMESPACE} 0\n"
                   for x in [*range(x1, x2, 16), x2] for z in [*range(z1, z2, 16), z2])


def _write_model(mc_dir, name, names, entry):
    structures = mcf.structure_dirs(mc_dir)[0]
    parts = _own_parts(mcf.find_nbt(structures, name), name, names)
    delete_parts = _own_parts(mcf.find_delete_nbt(structures, name), name, names)
    folder = f"models/{name}"
    if "extent" not in entry:
        entry["extent"] = _model_extent(mc_dir, parts)

    placed_line = f"function {NAMESPACE}:{folder}/placed\n"
    _write_function(mc_dir, f"{folder}/build", mcf.nbt_function_text(parts) + placed_line)
    _write_function(mc_dir, f"{folder}/placed", f'function {NAMESPACE}:remember {{name:"{name}"}}\n')
    _write_function(mc_dir, f"{folder}/queue", f'function {NAMESPACE}:build/trigger {{name:"{name}"}}\n')
    _write_function(mc_dir, f"{folder}/delete", f'function {NAMESPACE}:delete/start {{name:"{name}"}}\n')
    _write_function(mc_dir, f"{folder}/clear", mcf.nbt_delete_function_text(delete_parts))
    _write_function(mc_dir, f"{folder}/load", _forceload_lines("add", entry["extent"]))
    _write_function(mc_dir, f"{folder}/unload", _forceload_lines("remove", entry["extent"]))
    _write_function(mc_dir, f"{folder}/loaded", _chunks_loaded_text(entry["extent"]))

    # /function protein:... stays the way to do it by hand, and takes part in the same records
    for directory in mcf.function_dirs(mc_dir):
        if not os.path.isdir(directory):
            continue
        for filename in os.listdir(directory):
            if mcf._is_model_file(filename, name, ".mcfunction", prefixes=("build_",)):
                path = os.path.join(directory, filename)
                if filename == f"build_{name}.mcfunction":
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(_build_text(name))
                else:
                    _append_line(path, placed_line)
        with open(os.path.join(directory, f"clear_{name}.mcfunction"), "w", encoding="utf-8") as f:
            f.write(_clear_text(name))


def _append_line(path, line):
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    if line not in text:
        with open(path, "a", encoding="utf-8") as f:
            f.write(line)


def _build_text(name):
    # Before macros (Minecraft 1.20.2) `queue` can't load, #found stays 0 and the model is built on the spot
    return (f"scoreboard players set #found {NAMESPACE} 0\n"
            f"function {NAMESPACE}:models/{name}/queue\n"
            f"execute if score #found {NAMESPACE} matches 0 run function {NAMESPACE}:models/{name}/build\n")


def _clear_text(name):
    return (f"scoreboard players set #found {NAMESPACE} 0\n"
            f"function {NAMESPACE}:models/{name}/delete\n"
            f"execute if score #found {NAMESPACE} matches 0 run "
            "say Removing... must be standing on original obsidian block.\n"
            f"execute if score #found {NAMESPACE} matches 0 run function {NAMESPACE}:models/{name}/clear\n")


# --- functions of the whole world ---

def _per_model_objectives(name):
    return [f"{trigger}_{name}" for trigger in NUMBER_TRIGGERS]


def _load_text(registry):
    lines = [f"scoreboard objectives add {NAMESPACE} dummy\n"]
    lines += [f"scoreboard objectives add {objective} trigger\n" for objective in ("models", *NUMBER_TRIGGERS, "spawn")]
    for name in sorted(registry["models"]):
        lines += [f"scoreboard objectives add {objective} trigger\n" for objective in _per_model_objectives(name)]
    for name in registry["retired"]:
        lines += [f"scoreboard objectives remove {objective}\n" for objective in _per_model_objectives(name)]
    # A build or delete interrupted by a reload or restart picks up where it stopped
    lines += [f"schedule clear {NAMESPACE}:job/wait\n",
              f"scoreboard players set #busy {NAMESPACE} 0\n",
              f"function {NAMESPACE}:job/next\n"]
    return "".join(lines)


def _tick_text(registry):
    lines = [f"scoreboard players enable @a {objective}\n" for objective in ("models", *NUMBER_TRIGGERS, "spawn")]
    for name in sorted(registry["models"]):
        lines += [f"scoreboard players enable @a {objective}\n" for objective in _per_model_objectives(name)]
    lines += ["execute as @a[scores={models=1..}] run function " + NAMESPACE + ":list\n",
              "scoreboard players set @a[scores={models=1..}] models 0\n",
              "execute as @a[scores={build=1..}] at @s run function " + NAMESPACE + ":number/build\n",
              "execute as @a[scores={delete=1..}] run function " + NAMESPACE + ":number/delete\n",
              "execute as @a[scores={plot=1..}] run function " + NAMESPACE + ":number/plot\n",
              # Not `at @s`: a tick function runs at the world spawn, which is the position `spawn` wants
              "execute as @a[scores={spawn=1..}] run function " + NAMESPACE + ":spawn\n"]
    for name in sorted(registry["models"]):
        for trigger, action in _model_actions(name).items():
            objective = f"{trigger}_{name}"
            at_player = " at @s" if trigger == "build" else ""
            lines += [f"execute as @a[scores={{{objective}=1..}}]{at_player} run {action}\n",
                      f"scoreboard players set @a[scores={{{objective}=1..}}] {objective} 0\n"]
    return "".join(lines)


def _model_actions(name):
    return {"build": f'function {NAMESPACE}:build/trigger {{name:"{name}"}}',
            "delete": f'function {NAMESPACE}:delete/trigger {{name:"{name}"}}',
            "plot": f'function {NAMESPACE}:plot/trigger {{name:"{name}"}}'}


def _number_text(trigger, registry):
    """The function behind `/trigger <trigger> set <number>`, run as the player."""
    lines = [f"tag @s add {NAMESPACE}_miss\n"]
    for name, entry in sorted(registry["models"].items(), key=lambda item: item[1]["number"]):
        number = entry["number"]
        lines += [f"execute if score @s {trigger} matches {number} run tag @s remove {NAMESPACE}_miss\n",
                  f"execute if score @s {trigger} matches {number} run {_model_actions(name)[trigger]}\n"]
    message = json.dumps({"text": "There is no model with that number. List them with /trigger models",
                          "color": "red"})
    lines += [f"tellraw @s[tag={NAMESPACE}_miss] {message}\n",
              f"tag @s remove {NAMESPACE}_miss\n",
              f"scoreboard players set @s {trigger} 0\n"]
    return "".join(lines)


def _list_text(registry):
    if not registry["models"]:
        message = json.dumps({"text": "No PDB2MC models in this world yet.", "color": "gold"})
        return f"tellraw @s {message}\n"
    lines = [f"tellraw @s {json.dumps({'text': 'PDB2MC models (number, name, copies in the world):', 'color': 'gold'})}\n"]
    for name, entry in sorted(registry["models"].items(), key=lambda item: item[1]["number"]):
        details = "  ".join(str(entry[key]) for key in ("mode",) if entry.get(key))
        text = [{"text": f"{entry['number']}  ", "color": "yellow"},
                {"text": name, "color": "aqua"},
                {"text": f"  {details}  " if details else "  ", "color": "gray"},
                {"score": {"name": "#count", "objective": NAMESPACE}, "color": "white"},
                {"text": " in the world", "color": "gray"}]
        lines += [f"scoreboard players set #count {NAMESPACE} 0\n",
                  f"execute store result score #count {NAMESPACE} run data get storage {NAMESPACE}:models "
                  f'placed."{name}"\n',
                  f"tellraw @s {json.dumps(text)}\n"]
    usage = {"text": "/trigger build set <number> or /trigger build_<name>; the same with delete and plot",
             "color": "gray"}
    lines.append(f"tellraw @s {json.dumps(usage)}\n")
    return "".join(lines)


# Functions that are the same for every world. Lines starting with $ are macros, filled in by Minecraft.
_AT = "execute in $(dim) positioned $(x) $(y) $(z)"
_STATIC_FUNCTIONS = {
    # Note the current position and dimension in pdb2mc:run here
    "here": f"""summon marker ~ ~ ~ {{Tags:["{NAMESPACE}_here"]}}
execute store result storage {NAMESPACE}:run here.x int 1 run data get entity @e[type=marker,tag={NAMESPACE}_here,limit=1] Pos[0]
execute store result storage {NAMESPACE}:run here.y int 1 run data get entity @e[type=marker,tag={NAMESPACE}_here,limit=1] Pos[1]
execute store result storage {NAMESPACE}:run here.z int 1 run data get entity @e[type=marker,tag={NAMESPACE}_here,limit=1] Pos[2]
kill @e[type=marker,tag={NAMESPACE}_here]
data modify storage {NAMESPACE}:run here.dim set value "minecraft:overworld"
execute if dimension minecraft:the_nether run data modify storage {NAMESPACE}:run here.dim set value "minecraft:the_nether"
execute if dimension minecraft:the_end run data modify storage {NAMESPACE}:run here.dim set value "minecraft:the_end"
""",
    # Run at a build's position, with the model's name: note where the copy is
    "remember": f"""function {NAMESPACE}:here
$data modify storage {NAMESPACE}:run here.name set value "$(name)"
function {NAMESPACE}:remember_at with storage {NAMESPACE}:run here
""",
    # A second build at the same spot is the same copy
    "remember_at": f"""$execute unless data storage {NAMESPACE}:models placed."$(name)"[{{x:$(x),y:$(y),z:$(z),dim:"$(dim)"}}] run data modify storage {NAMESPACE}:models placed."$(name)" append value {{x:$(x),y:$(y),z:$(z),dim:"$(dim)"}}
""",
    "spawn": """tp @s ~ ~ ~
scoreboard players set @s spawn 0
""",
    "plot/trigger": f"""$execute unless data storage {NAMESPACE}:models placed."$(name)"[-1] run tellraw @s {{"text":"$(name) has not been built in this world yet. Build it with /trigger build_$(name)","color":"red"}}
$execute if data storage {NAMESPACE}:models placed."$(name)"[-1] run function {NAMESPACE}:plot/go with storage {NAMESPACE}:models placed."$(name)"[-1]
$execute if data storage {NAMESPACE}:models placed."$(name)"[-1] run tellraw @s {{"text":"$(name)","color":"aqua"}}
""",
    "plot/go": f"""${_AT} run tp @s ~ ~ ~ facing ~40 ~10 ~40
""",
    # Builds and deletes wait for their chunks, in one queue, so a player's request is never half done
    "build/trigger": f"""scoreboard players set #found {NAMESPACE} 1
function {NAMESPACE}:here
$data modify storage {NAMESPACE}:run here.name set value "$(name)"
data modify storage {NAMESPACE}:run here.action set value "build"
data modify storage {NAMESPACE}:run jobs append from storage {NAMESPACE}:run here
execute unless score #busy {NAMESPACE} matches 1 run function {NAMESPACE}:job/next
""",
    "build/run": f"""${_AT} run function {NAMESPACE}:models/$(name)/build
function {NAMESPACE}:job/finish with storage {NAMESPACE}:run jobs[0]
""",
    "delete/trigger": f"""scoreboard players set #found {NAMESPACE} 0
$function {NAMESPACE}:delete/start {{name:"$(name)"}}
$execute if score #found {NAMESPACE} matches 0 run tellraw @s {{"text":"$(name) is not in this world, so there is nothing to delete.","color":"red"}}
""",
    # Take the newest copy off the model's list and queue it; #found tells the caller there was one
    "delete/start": f"""$execute if data storage {NAMESPACE}:models placed."$(name)"[-1] run function {NAMESPACE}:delete/queue {{name:"$(name)"}}
""",
    "delete/queue": f"""scoreboard players set #found {NAMESPACE} 1
$data modify storage {NAMESPACE}:run jobs append from storage {NAMESPACE}:models placed."$(name)"[-1]
$data modify storage {NAMESPACE}:run jobs[-1].name set value "$(name)"
data modify storage {NAMESPACE}:run jobs[-1].action set value "delete"
$data remove storage {NAMESPACE}:models placed."$(name)"[-1]
execute unless score #busy {NAMESPACE} matches 1 run function {NAMESPACE}:job/next
""",
    "delete/run": f"""${_AT} run function {NAMESPACE}:models/$(name)/clear
${_AT} if block ~ ~-1 ~ minecraft:obsidian run setblock ~ ~-1 ~ minecraft:air
$tellraw @a {{"text":"Removed $(name) at $(x) $(y) $(z)","color":"green"}}
function {NAMESPACE}:job/finish with storage {NAMESPACE}:run jobs[0]
""",
    "job/next": f"""execute unless data storage {NAMESPACE}:run jobs[0] run scoreboard players set #busy {NAMESPACE} 0
execute if data storage {NAMESPACE}:run jobs[0] run function {NAMESPACE}:job/begin
""",
    "job/begin": f"""scoreboard players set #busy {NAMESPACE} 1
scoreboard players set #wait {NAMESPACE} 0
function {NAMESPACE}:job/load with storage {NAMESPACE}:run jobs[0]
function {NAMESPACE}:job/wait
""",
    "job/load": f"""${_AT} run function {NAMESPACE}:models/$(name)/load
""",
    # `schedule` can't pass arguments, so this plain function looks them up for job/try
    "job/wait": f"""function {NAMESPACE}:job/try with storage {NAMESPACE}:run jobs[0]
""",
    "job/try": f"""scoreboard players add #wait {NAMESPACE} 1
scoreboard players set #ready {NAMESPACE} 1
${_AT} run function {NAMESPACE}:models/$(name)/loaded
$execute if score #ready {NAMESPACE} matches 0 if score #wait {NAMESPACE} matches 1 run tellraw @a {{"text":"Getting the area ready for $(name)...","color":"gray"}}
execute if score #ready {NAMESPACE} matches 0 if score #wait {NAMESPACE} matches ..{WAIT_TRIES} run schedule function {NAMESPACE}:job/wait {WAIT_TICKS}t
execute if score #ready {NAMESPACE} matches 0 if score #wait {NAMESPACE} matches {WAIT_TRIES + 1}.. run function {NAMESPACE}:job/give_up with storage {NAMESPACE}:run jobs[0]
$execute if score #ready {NAMESPACE} matches 1 run function {NAMESPACE}:$(action)/run with storage {NAMESPACE}:run jobs[0]
""",
    # A copy that could not be deleted goes back on its list, so nothing is forgotten
    "job/give_up": f"""$tellraw @a {{"text":"Could not load the area at $(x) $(y) $(z), so $(name) was not changed.","color":"red"}}
data modify storage {NAMESPACE}:run action set from storage {NAMESPACE}:run jobs[0].action
$execute if data storage {NAMESPACE}:run {{action:"delete"}} run data modify storage {NAMESPACE}:models placed."$(name)" append from storage {NAMESPACE}:run jobs[0]
function {NAMESPACE}:job/finish with storage {NAMESPACE}:run jobs[0]
""",
    "job/finish": f"""${_AT} run function {NAMESPACE}:models/$(name)/unload
data remove storage {NAMESPACE}:run jobs[0]
function {NAMESPACE}:job/next
""",
}


def _write_tags(mc_dir):
    tags = os.path.join(_pack_dir(mc_dir), "data", "minecraft", "tags")
    for folder in mcf.FUNCTION_DIRS:
        directory = os.path.join(tags, folder)
        os.makedirs(directory, exist_ok=True)
        for name in ("load", "tick"):
            # required: false, so a version that can't load the function doesn't lose the whole tag
            with open(os.path.join(directory, f"{name}.json"), "w", encoding="utf-8") as f:
                json.dump({"values": [{"id": f"{NAMESPACE}:{name}", "required": False}]}, f)


def sync(mc_dir):
    """
    Bring the world's trigger functions in line with the models it holds, which picks up models built before
    this feature existed and drops models whose files are gone. Safe to repeat.
    """
    registry = _load_registry(mc_dir)
    known = registry["models"]
    present = _world_models(mc_dir)

    for name in [name for name in known if name not in present]:
        del known[name]
        if name not in registry["retired"]:
            registry["retired"].append(name)
    taken = {entry["number"] for entry in known.values() if "number" in entry}
    for name in present:
        entry = known.setdefault(name, {})
        if "number" not in entry:
            entry["number"] = _next_number(taken)
            taken.add(entry["number"])
    registry["retired"] = [name for name in registry["retired"] if name not in known]

    for root in _function_roots(mc_dir):
        shutil.rmtree(os.path.join(root, "models"), ignore_errors=True)
    for name in present:
        _write_model(mc_dir, name, present, known[name])

    for path, text in _STATIC_FUNCTIONS.items():
        _write_function(mc_dir, path, text)
    _write_function(mc_dir, "load", _load_text(registry))
    _write_function(mc_dir, "tick", _tick_text(registry))
    _write_function(mc_dir, "list", _list_text(registry))
    for trigger in NUMBER_TRIGGERS:
        _write_function(mc_dir, f"number/{trigger}", _number_text(trigger, registry))
    _write_tags(mc_dir)
    _save_registry(mc_dir, registry)
    return registry


def install_model(mc_dir, name, mode=None, scale=None):
    """Give a freshly built model its in-game commands. Returns its number."""
    name = name.lower()
    registry = _load_registry(mc_dir)
    entry = registry["models"].setdefault(name, {})
    entry.update({key: value for key, value in (("mode", mode), ("scale", scale)) if value is not None})
    # A rebuild may have changed the model's size
    entry.pop("extent", None)
    _save_registry(mc_dir, registry)
    return sync(mc_dir)["models"][name]["number"]


def commands(name, number=None):
    """The in-game commands of a model. The desktop window lays them out in UI/messages.py."""
    build_trigger = f"/trigger build_{name}"
    return {
        "reload": "/reload",
        "function": f"/function protein:build_{name}",
        "build_trigger": build_trigger,
        "build_triggers": build_trigger if number is None else f"{build_trigger} or /trigger build set {number}",
        #"build_triggers": build_trigger,
        "list_models": "/trigger models",
        "delete": f"/trigger delete_{name}",
        "teleport": f"/trigger plot_{name}",
    }


def instructions(name, number=None):
    """The in-game commands of a model as plain text, for the command line."""
    command = commands(name, number)
    return (f"INSTRUCTIONS for {name}:\n"
            f"First reload the world with {command['reload']}, then build it with:\n"
            f"    {command['function']} (works in all Minecraft versions)\n\n"
            f"or use Trigger functions:\n"
            f"    {command['build_triggers']}\n"
            f"    List your models with {command['list_models']}\n"
            f"    Delete it from anywhere with {command['delete']}\n"
            f"    Teleport to it with {command['teleport']}\n")
