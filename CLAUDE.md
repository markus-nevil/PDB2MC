# PDB2MC

Turns protein / nucleic acid structures (.pdb, .cif) into Minecraft models. `PDB2MC/` is the engine and command line,
`UI/` the PyQt6 desktop program, `web/` the web version (FastAPI server + frontend), `tests/` the desktop tests.

## Every change: integration tests

Run all of these before saying a change is done, and report the results (pass counts, or the failures):

1. **The whole test suite**, not only the tests near the change: `python -m pytest -q` from the repository root.
   Many tests are integration tests: they build models into a temporary Minecraft world and check the files and
   functions, and drive the real windows (Qt runs headless in tests).
   - The venv has no pytest. Install the test tools outside it rather than changing the venv:
     `venv/Scripts/python -m pip install --target <scratch>/testdeps pytest pytest-qt`, then run with
     `PYTHONPATH=<scratch>/testdeps`.
2. **CI's package versions**: CI installs the newest packages (NumPy 2, pandas 3, PyQt6 6.12 or later); the venv is
   older (NumPy 1, PyQt6 6.6). For changes to numerical code, the windows or dependencies, also run the suite with
   `pip install --target <scratch>/ci_latest ".[test]"` on PYTHONPATH (delete the PDB2MC/UI copies it installs
   there, so the repository's code is tested).
3. **An end-to-end build** for changes to the engine or a mode: build a real model through the command line into a
   temporary world, e.g. `python -m PDB2MC.cli Ribbon UI/presets/GFP.pdb <scratch>/saves/world --scale 1`, and
   check it finishes and writes structure files. For large-model work use a big structure such as 8VKR (.cif).
4. **The web tests** for changes to `PDB2MC/` or `web/`: `web/tests/test_web.py` (needs the packages in
   `web/server/requirements.txt`).
5. **A packaged build** for changes to packaging, data files, images or imports: build the .exe with the command at
   the bottom of `setup.py` (into a scratch folder) and launch it.

Output that must not change (speed-ups, refactors) is compared block for block against the previous code.

## Every change: security checks

1. **Static scan**: run `bandit -r PDB2MC UI web/server -q` (install it outside the venv like pytest) and look at
   anything new in the changed code.
2. **Dependencies**: when dependencies change, and before a release, run `pip-audit` on the desktop and web
   requirements (`setup.py`, `web/server/requirements.txt`).
3. **Review the risky areas** whenever a change touches them, and say what was checked:
   - files and text from users or the internet: uploads to the web server, structure files, PDB IDs
     (`PDB2MC/fetch.py` only accepts IDs matching its pattern), model names (`build.custom_model_name`)
   - anything that becomes a path, a Minecraft command or HTML: no path traversal, no command injection into
     .mcfunction files, values in message windows stay escaped (`UI/messages.py`)
   - network access: HTTPS only, timeouts, no user data sent anywhere
4. For a whole branch, the `/security-review` command reviews the pending changes.

Report findings with how serious they are; fix real problems as part of the change, and ask before larger changes.

## Working in this repository

- Branch from `main` for new work; commit and push only when asked. PRs go to `main` on GitHub
  (markus-nevil/PDB2MC; the local remote still uses the old name mcpdb and redirects).
- Message window wording lives in `UI/messages.py`, tool tips in `UI/tooltips.py`, colour schemes in
  `PDB2MC/color_schemes.py`.
- Large structures (more than about 60 chains) should be loaded as .cif; the .pdb format can't name that many chains.
- **Version number: every change raises it.** When making a change while `PDB2MC/version.py` still holds the
  latest released version (`gh release list`), raise the last number by one (2.0.4 -> 2.0.5) in the same change.
  If the version is already ahead of the latest release, the next release isn't out yet: keep it. Update every
  mention together: `PDB2MC/version.py` and the `Version:` line at the top of `README.md` (setup.py, the welcome
  window, the update check and the release workflow read version.py). `tests/test_version.py` checks they agree.
  A bigger jump (2.1.0, 3.0.0) only when asked. `web/frontend/package.json` has its own version; leave it.
- Releases are tagged `v<version>` from `PDB2MC/version.py`; the program's update check reads the latest release.
  Pushing the tag runs `.github/workflows/release.yml`, which tests, builds PDB2MC.exe from the exact versions in
  `requirements-build.txt` and attaches it to the release. Changing a dependency means updating that file too (see
  its header), with a pip-audit of it.
