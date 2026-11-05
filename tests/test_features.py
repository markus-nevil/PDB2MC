"""Faster ribbons, colour schemes, downloading by PDB ID and the size estimate."""
import gzip
import os

import numpy as np
import pandas as pd
import pytest
import requests

from PDB2MC import build, cli, color_schemes, defaults, fetch, pdb_manipulation as pdbm
from PDB2MC.structure_data import StructureData
from conftest import pdb_line, preset


class Captured(build.ModelBuilder):
    """Builds without writing a world, keeping each part's blocks with their final atom labels."""

    def write(self, blocks, suffix, atoms=None, block_lookup=None):
        if blocks is None or blocks.empty:
            return []
        if self.residue_labels is not None:
            blocks = build.recolor_by_residue(blocks, self.df if atoms is None else atoms, self.residue_labels)
        self.parts[suffix] = blocks
        return []


def capture(mode, name, scale=1, **settings):
    path = preset(name)
    config = defaults.default_config(mode)
    config.update(scale=scale, pdb_file=path, **settings)
    builder = Captured(config, StructureData.from_file(path), ".", name="t")
    builder.parts = {}
    build.mode_module(mode).build(builder)
    return builder


# --- ribbon speed: the same blocks as before ---

@pytest.mark.parametrize("name, scale, settings, blocks", [
    ("Helix", 2, {}, 260),
    ("GFP", 1, {}, 825),
    ("GFP", 1, {"bar_style": True}, 701),
    ("DNA", 2, {}, 6602),
])
def test_ribbon_blocks_unchanged(name, scale, settings, blocks):
    # Block counts of the ribbon parts as built before the calculations were sped up
    parts = capture("Ribbon", name, scale, **settings).parts
    unique = sum(len(part.drop_duplicates(subset=['X', 'Y', 'Z'])) for suffix, part in parts.items()
                 if suffix.endswith(("_ribbon", "_backbone")))
    assert unique == blocks


def test_batch_lines_match_single_lines():
    rng = np.random.default_rng(0)
    starts = rng.integers(-30, 30, (3000, 3))
    ends = starts + rng.integers(-20, 21, (3000, 3))
    ends[:100] = starts[:100]
    points, line = pdbm.bresenham_lines(starts, ends)
    single = [pdbm.bresenham_line(*s, *e).reshape(-1, 3) for s, e in zip(starts.tolist(), ends.tolist())]
    assert np.array_equal(points, np.concatenate(single))
    assert np.array_equal(line, np.repeat(np.arange(len(single)), [len(s) for s in single]))


def test_vectors_pair_each_c_with_its_o():
    df = pd.DataFrame({'atom': ['N', 'C', 'O', 'C', 'C', 'O'], 'resid': [1, 1, 1, 2, 3, 3],
                       'residue': ['ALA'] * 6, 'chain': ['A'] * 6,
                       'X': [0, 1, 1, 5, 9, 9], 'Y': [0, 0, 2, 0, 0, -1], 'Z': [0, 0, 0, 0, 0, 0]})
    vectors = pdbm.CO_vectors(df, width=2)
    assert vectors['resid'].tolist() == [1, 3]
    assert vectors[['X', 'Y', 'Z']].to_numpy().tolist() == [[0, 4, 0], [0, -2, 0]]


def test_ribbon_flank_refuses_repeated_residue_numbers():
    vectors = pd.DataFrame({'X': [1, 1], 'Y': [0, 0], 'Z': [0, 0], 'resid': [5, 5]})
    with pytest.raises(ValueError):
        pdbm.flank_coordinates(pd.DataFrame(columns=pdbm.FLANK_COLUMNS + ['structure']), vectors)


# --- colour schemes ---

def labels_of(builder, suffix):
    return set(builder.parts[suffix]['atom'].astype(str))


def test_molecule_scheme_colours_copies_alike():
    builder = capture("Ribbon", "Hemoglobin", color_scheme="Molecule")
    assert builder.numbers['A'] == builder.numbers['C'] != builder.numbers['B'] == builder.numbers['D']


def test_chain_scheme_is_the_default():
    builder = capture("Ribbon", "Hemoglobin")
    assert len(set(builder.numbers.values())) == 4 and builder.residue_labels is None


@pytest.mark.parametrize("mode", ["Skeleton", "Custom", "Ribbon", "Space Filling"])
def test_residue_schemes_replace_chain_colours_only(mode):
    builder = capture(mode, "GFP", by_chain=True, color_scheme="Hydrophobicity")
    labels = set().union(*(labels_of(builder, suffix) for suffix in builder.parts if 'atom' in builder.parts[suffix]))
    assert not any(build.CHAIN_LABEL.fullmatch(label) for label in labels)
    assert {f"hydrophobicity_{i}" for i in range(1, 6)} & labels
    if mode == "Custom":
        assert {"C", "O", "N"} <= labels_of(builder, "atoms")     # atoms keep their element colours


def test_scheme_needs_colour_by_chain():
    builder = capture("Skeleton", "GFP", by_chain=False, color_scheme="Charge")
    assert builder.scheme == "Chain" and labels_of(builder, "backbone") == {"backbone_atom"}


def test_charge_scheme_makes_dna_negative():
    builder = capture("Ribbon", "DNA", by_chain=True, color_scheme="Charge")
    assert {label for suffix in builder.parts if suffix.endswith("_backbone")
            for label in labels_of(builder, suffix)} == {"charge_negative"}


def test_scheme_labels_of_residues():
    assert color_schemes.hydrophobicity_label("ILE") == "hydrophobicity_5"
    assert color_schemes.hydrophobicity_label("ARG") == "hydrophobicity_1"
    assert color_schemes.hydrophobicity_label("HOH") == color_schemes.OTHER
    assert [color_schemes.charge_label(r) for r in ("LYS", "GLU", "SER", "DG")] == \
        ["charge_positive", "charge_negative", "charge_neutral", "charge_negative"]


def test_confidence_from_b_factors_and_plddt():
    values = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
    experimental = color_schemes.confidence_labels(values, predicted=False).tolist()
    assert experimental[0] == "confidence_1" and experimental[-1] == "confidence_4"
    predicted = color_schemes.confidence_labels(pd.Series([95.0, 80.0, 60.0, 30.0]), predicted=True).tolist()
    assert predicted == ["confidence_1", "confidence_2", "confidence_3", "confidence_4"]
    assert set(color_schemes.confidence_labels(pd.Series([None, None]), False)) == {color_schemes.OTHER}


def test_b_factors_are_read(write_pdb):
    line = pdb_line("ATOM", 1, "CA", "ALA", "A", 1, 0, 0, 0, "C")
    line = line[:60] + f"{37.5:6.2f}" + line[66:]
    s = StructureData.from_pdb(write_pdb(line))
    assert s.atoms[0]['bfactor'] == 37.5 and s.metadata['predicted'] is False
    gfp = StructureData.from_file(preset("GFP"))
    assert all(a['bfactor'] is not None for a in gfp.atoms)


def test_every_scheme_block_is_a_block():
    from PDB2MC.variables import decorative_blocks
    assert set(color_schemes.BLOCKS.values()) <= set(decorative_blocks)


# --- downloading by PDB ID ---

class FakeResponse:
    def __init__(self, status, body=b""):
        self.status_code, self.body = status, body
        self.headers = {"Content-Length": str(len(body))}

    def iter_content(self, size):
        for start in range(0, len(self.body), size):
            yield self.body[start:start + size]

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False


class FakeSession:
    def __init__(self, response=None, error=None):
        self.response, self.error, self.urls = response, error, []

    def get(self, url, **kwargs):
        self.urls.append(url)
        if self.error:
            raise self.error
        return self.response


@pytest.mark.parametrize("text, normal", [("1gfl", "1GFL"), (" 4HHB ", "4HHB"), ("pdb_00001gfl", "pdb_00001gfl"),
                                          ("GFP", None), ("12345", None), ("abcd", None), ("", None)])
def test_pdb_ids(text, normal):
    assert fetch.normalize_id(text) == normal


def test_download_saves_and_reuses(tmp_path):
    with open(preset("Helix"), "rb") as f:
        text = f.read()
    session = FakeSession(FakeResponse(200, gzip.compress(text)))
    seen = []
    path = fetch.download("1abc", folder=str(tmp_path), progress=lambda done, total: seen.append((done, total)),
                          session=session)
    assert path == str(tmp_path / "1ABC.cif") and open(path, "rb").read() == text
    assert session.urls == ["https://files.rcsb.org/download/1ABC.cif.gz"] and seen[-1][0] == seen[-1][1]
    fetch.download("1ABC", folder=str(tmp_path), session=session)
    assert len(session.urls) == 1          # downloaded once


def test_download_errors(tmp_path):
    with pytest.raises(fetch.NoSuchEntry):
        fetch.download("0zzz", folder=str(tmp_path), session=FakeSession(FakeResponse(404)))
    with pytest.raises(fetch.DownloadError, match="internet"):
        fetch.download("1abc", folder=str(tmp_path), session=FakeSession(error=requests.ConnectionError("offline")))
    with pytest.raises(fetch.DownloadError, match="damaged"):
        fetch.download("1abc", folder=str(tmp_path), session=FakeSession(FakeResponse(200, b"not gzip")))
    with pytest.raises(fetch.DownloadError, match="not a PDB ID"):
        fetch.download("GFP", folder=str(tmp_path))
    assert os.listdir(tmp_path) == []      # nothing half-written is left to be reused


def test_command_line_downloads_a_pdb_id(tmp_path, monkeypatch):
    world = tmp_path / "saves" / "world"
    world.mkdir(parents=True)
    asked = []
    monkeypatch.setattr(fetch, "download", lambda pdb_id: asked.append(pdb_id) or preset("Helix"))
    assert cli.main(["Skeleton", "1abc", str(world)]) == 0
    assert asked == ["1abc"]


# --- size estimate ---

def test_model_size_grows_with_scale():
    structure = StructureData.from_file(preset("GFP"))
    config = defaults.default_config("Skeleton")
    small = build.model_size(structure, {**config, 'scale': 1}, "Skeleton")
    large = build.model_size(structure, {**config, 'scale': 2}, "Skeleton")
    assert small['height'] <= small['width'] <= small['depth']
    assert abs(large['width'] - 2 * small['width']) <= 3 and large['chunks'] > small['chunks']
    assert not small['too_tall'] and not small['large']
    huge = build.model_size(structure, {**config, 'scale': 10}, "Skeleton")
    assert huge['too_tall'] and huge['large']


def test_model_size_matches_a_real_build():
    builder = capture("Skeleton", "GFP")
    blocks = pd.concat([p[['X', 'Y', 'Z']] for p in builder.parts.values()])
    built = sorted((blocks.max() - blocks.min() + 1).astype(int).tolist())
    config = defaults.default_config("Skeleton")
    size = build.model_size(builder.structure, {**config, 'scale': 1}, "Skeleton")
    estimate = [size['height'], size['width'], size['depth']]
    assert all(abs(a - b) <= 3 for a, b in zip(estimate, built))
