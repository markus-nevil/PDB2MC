"""Every mention of PDB2MC's version number says the same thing (see CLAUDE.md: the version rises with each change)."""
import os
import re

from PDB2MC.version import version

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_version_is_three_numbers():
    assert re.fullmatch(r"\d+\.\d+\.\d+", version)


def test_readme_shows_the_same_version():
    with open(os.path.join(REPO, "README.md"), encoding="utf-8") as f:
        mentions = re.findall(r"Version:\s*v?(\d+\.\d+\.\d+)", f.read())
    assert mentions and set(mentions) == {version}
