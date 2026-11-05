"""
Settings the user keeps between runs of PDB2MC, stored as settings.json in the user's own settings folder:

    Windows  %APPDATA%\\PDB2MC\\settings.json
    macOS    ~/Library/Application Support/PDB2MC/settings.json
    Linux    $XDG_CONFIG_HOME/PDB2MC/settings.json (usually ~/.config)

The file never lives next to the program: a --onefile PyInstaller .exe unpacks itself to a temporary
folder that is deleted on exit, so anything saved beside the code would be lost, and Program Files is
not writable. A missing or damaged file gives the defaults; a damaged one is kept as settings.json.bad.
"""
import json
import os
import sys
import tempfile

from PDB2MC import defaults
from PDB2MC.variables import decorative_blocks

SETTINGS_FILE = "settings.json"
# Points the settings somewhere else (used by the tests)
DIRECTORY_VARIABLE = "PDB2MC_SETTINGS_DIR"


def settings_dir():
    override = os.environ.get(DIRECTORY_VARIABLE)
    if override:
        return override
    home = os.path.expanduser("~")
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.join(home, "AppData", "Roaming")
    elif sys.platform == "darwin":
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(home, ".config")
    return os.path.join(base, "PDB2MC")


def settings_path():
    return os.path.join(settings_dir(), SETTINGS_FILE)


def load():
    """All saved settings as a dict; empty when there are none or the file can't be read."""
    path = settings_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            settings = json.load(f)
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    except ValueError:
        try:
            os.replace(path, path + ".bad")
        except OSError:
            pass
        return {}
    return settings if isinstance(settings, dict) else {}


def save(settings):
    """Write the settings; a temporary file and rename, so a crash can't leave half a file behind."""
    directory = settings_dir()
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=SETTINGS_FILE, suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, sort_keys=True)
        os.replace(temporary, settings_path())
    except BaseException:
        if os.path.exists(temporary):
            os.remove(temporary)
        raise


def update(**changes):
    settings = load()
    settings.update(changes)
    save(settings)


# --- metal ions ---

def metal_blocks():
    """Block of every metal ion: the defaults with the user's choices on top. Works for every mode."""
    saved = load().get("metal_blocks")
    blocks = defaults.default_metal_blocks()
    if isinstance(saved, dict):
        blocks.update({metal: block for metal, block in saved.items()
                       if metal in blocks and block in decorative_blocks})
    return blocks


def set_metal_blocks(blocks):
    """Save the choices that differ from the defaults, so later changes of a default still take effect."""
    standard = defaults.default_metal_blocks()
    update(metal_blocks={metal: block for metal, block in blocks.items()
                         if metal in standard and block != standard[metal]})


# --- structure files ---

def structure_dir():
    """The folder the "Select PDB File" dialog opens in, or "" when none is set or it no longer exists."""
    folder = load().get("structure_dir")
    return folder if isinstance(folder, str) and os.path.isdir(folder) else ""


def saved_structure_dir():
    """The folder as saved, even if it is missing right now (for example a USB stick that is unplugged)."""
    folder = load().get("structure_dir")
    return folder if isinstance(folder, str) else ""


def set_structure_dir(folder):
    update(structure_dir=folder or "")
