"""
Downloading a structure by its PDB ID from the RCSB Protein Data Bank.

Structures are fetched as mmCIF, the format the Protein Data Bank keeps every entry in: large structures have
no .pdb file at all, and the .pdb format cannot name more than about 60 chains. They are saved in the
"structures" folder next to the settings (see user_settings) and reused the next time the same ID is asked for.
"""
import gzip
import os
import re

import requests

from PDB2MC import user_settings

DOWNLOAD_URL = "https://files.rcsb.org/download/{id}.cif.gz"
ENTRY_PAGE = "https://www.rcsb.org/structure/{id}"
# Classic 4-character IDs (1GFL) and the extended IDs the PDB will issue once those run out (pdb_00001gfl)
PDB_ID = re.compile(r"^(?:[0-9][a-z0-9]{3}|pdb_[0-9]{4}[0-9][a-z0-9]{3})$", re.IGNORECASE)
TIMEOUT = 30
CHUNK = 1 << 16
FOLDER = "structures"


class DownloadError(Exception):
    """A structure could not be downloaded; the message says why, for showing to the user."""


class NoSuchEntry(DownloadError):
    pass


def normalize_id(text):
    """The PDB ID in text as the Protein Data Bank writes it (1GFL), or None when it isn't one."""
    text = (text or "").strip()
    if not PDB_ID.match(text):
        return None
    return text.lower() if text.lower().startswith("pdb_") else text.upper()


def download_dir():
    return os.path.join(user_settings.settings_dir(), FOLDER)


def structure_path(pdb_id, folder=None):
    return os.path.join(folder or download_dir(), f"{pdb_id}.cif")


def download(pdb_id, folder=None, progress=None, session=None):
    """
    Path of the mmCIF file of pdb_id, downloading it unless it was downloaded before. progress, if given, is
    called with (bytes so far, total bytes or None) as it downloads. Raises NoSuchEntry for an unknown ID and
    DownloadError when the download fails.
    """
    normal = normalize_id(pdb_id)
    if normal is None:
        raise DownloadError(f"'{pdb_id}' is not a PDB ID. PDB IDs are four characters, such as 1GFL.")
    path = structure_path(normal, folder)
    if os.path.isfile(path) and os.path.getsize(path) > 0:
        return path
    report = progress or (lambda done, total: None)
    getter = session or requests
    url = DOWNLOAD_URL.format(id=normal)
    try:
        response = getter.get(url, stream=True, timeout=TIMEOUT)
    except requests.RequestException as e:
        raise DownloadError(f"Could not reach the Protein Data Bank. Check the internet connection. ({e})") from e
    with response:
        if response.status_code == 404:
            raise NoSuchEntry(f"The Protein Data Bank has no entry {normal}.")
        if response.status_code != 200:
            raise DownloadError(f"The Protein Data Bank answered with error {response.status_code}.")
        total = response.headers.get("Content-Length")
        total = int(total) if total and total.isdigit() else None
        chunks, done = [], 0
        try:
            for chunk in response.iter_content(CHUNK):
                chunks.append(chunk)
                done += len(chunk)
                report(done, total)
        except requests.RequestException as e:
            raise DownloadError(f"The download of {normal} was interrupted. ({e})") from e
    try:
        text = gzip.decompress(b"".join(chunks))
    except (OSError, EOFError) as e:
        raise DownloadError(f"The file downloaded for {normal} is damaged. ({e})") from e
    os.makedirs(os.path.dirname(path), exist_ok=True)
    # Written under another name first, so a failed write never leaves a half file to be reused
    partial = path + ".part"
    with open(partial, "wb") as f:
        f.write(text)
    os.replace(partial, path)
    return path
