"""
Locations of files bundled with PDB2MC.

Replaces the old ``pkg_resources.resource_filename`` calls (pkg_resources has been removed from
current setuptools releases, so importing it fails on a fresh install). Works for a source
checkout, an installed package and a PyInstaller build (``--add-data "UI;UI"`` etc.).
"""
import os
import sys


def _root():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def package_file(name):
    """Path to a data file shipped inside the PDB2MC package (e.g. 'chains.txt', 'pack.mcmeta')."""
    return os.path.join(_root(), 'PDB2MC', name)


def ui_dir():
    """The UI directory. Relative paths such as 'images/icons/logo.png' resolve against it."""
    return os.path.join(_root(), 'UI')


def images_dir():
    return os.path.join(ui_dir(), 'images')


def presets_dir():
    return os.path.join(ui_dir(), 'presets')


def image(*parts):
    """Absolute path to an image, e.g. image('icons', 'icon_bad.png')."""
    return os.path.join(images_dir(), *parts)
