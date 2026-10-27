import numpy as np
import pandas as pd
import pytest

from PDB2MC import pdb_manipulation as pdbm, skeleton
from PDB2MC.structure_data import StructureData
from conftest import pdb_line, preset


def transform_matrix(fn):
    basis = pd.DataFrame(np.eye(3), columns=['X', 'Y', 'Z'])
    return fn(basis.copy())[['X', 'Y', 'Z']].to_numpy().T


@pytest.mark.parametrize("fn", [pdbm.rotate_x, pdbm.rotate_y, pdbm.rotate_z])
def test_rotations_are_proper_not_reflections(fn):
    m = transform_matrix(fn)
    assert np.allclose(m @ m.T, np.eye(3))
    assert np.isclose(np.linalg.det(m), 1.0), "a reflection would mirror the molecule (left-handed helices)"


@pytest.mark.parametrize("fn, axis", [(pdbm.rotate_x, 0), (pdbm.rotate_z, 2)])
def test_rotation_moves_the_named_axis_onto_y(fn, axis):
    m = transform_matrix(fn)
    assert np.allclose(m @ np.eye(3)[axis], [0, 1, 0])


def signed_volume(df):
    p = df[['X', 'Y', 'Z']].to_numpy(dtype=float)
    return np.linalg.det(np.stack([p[1] - p[0], p[2] - p[0], p[3] - p[0]]))


@pytest.mark.parametrize("shape", [(1, 5, 9), (5, 1, 9), (5, 9, 1)])
def test_rotate_to_y_preserves_handedness_and_flattens_y(shape):
    rng = np.random.default_rng(0)
    df = pd.DataFrame(rng.random((50, 3)) * shape, columns=['X', 'Y', 'Z'])
    df.loc[:3, ['X', 'Y', 'Z']] = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]]
    before = signed_volume(df)
    out = pdbm.rotate_to_y(df.copy())
    assert np.sign(signed_volume(out)) == np.sign(before)
    ranges = out[['X', 'Y', 'Z']].max() - out[['X', 'Y', 'Z']].min()
    assert ranges['Y'] == ranges.min()
    assert out['Y'].min() == 0


def dihedral(p0, p1, p2, p3):
    b0, b1, b2 = p0 - p1, p2 - p1, p3 - p2
    b1 = b1 / np.linalg.norm(b1)
    v = b0 - np.dot(b0, b1) * b1
    w = b2 - np.dot(b2, b1) * b1
    return np.degrees(np.arctan2(np.dot(np.cross(b1, v), w), np.dot(v, w)))


@pytest.mark.parametrize("name", ["Helix", "Nucleosome", "Hemoglobin"])
def test_helices_stay_right_handed(name):
    """The CA(i)..CA(i+3) dihedral of an alpha helix is about +50 degrees; a mirror image gives -50."""
    s = StructureData.from_pdb(preset(name))
    df = pdbm.structure_to_df(s)
    df = pdbm.rotate_to_y(pdbm.move_coordinates(pdbm.scale_coordinates(df, 1.0)))
    df = pdbm.add_structure_from_structured_data(df, s)
    ca = df[(df['atom'] == 'CA') & (df['row'] == 'ATOM')]
    angles = []
    for chain, c in ca.groupby('chain'):
        c = c.sort_values('resid')
        p, helix, resid = c[['X', 'Y', 'Z']].to_numpy(dtype=float), (c['structure'] == 'helix').to_numpy(), c['resid'].to_numpy()
        for i in range(len(c) - 3):
            if helix[i:i + 4].all() and resid[i + 3] - resid[i] == 3:
                angles.append(dihedral(*p[i:i + 4]))
    if not angles:
        pytest.skip("no helices")
    assert np.median(angles) > 30


def test_bresenham_lines_are_connected_and_exclude_the_end_point():
    for start, end in [((0, 0, 0), (7, 3, -2)), ((5, 5, 5), (5, -4, 5)), ((0, 0, 0), (-3, -3, -3))]:
        points = pdbm.bresenham_line(*start, *end)
        assert tuple(points[0]) == start
        assert len(points) == max(abs(e - s) for s, e in zip(start, end))
        steps = np.abs(np.diff(np.vstack([points, end]), axis=0))
        assert steps.max() <= 1


def reference_intermediate_points(replot_df, keep_columns=False, fill_columns=False):
    """The pre-optimisation implementation (one DataFrame per pair), kept to check equivalence."""
    columns = ['X', 'Y', 'Z']
    other_columns = replot_df.columns.drop(columns)
    coords = replot_df[columns].values
    chains = replot_df['chain'].values
    dfs = []
    for i in range(1, len(replot_df)):
        if chains[i - 1] == chains[i]:
            pts = pdbm.bresenham_line(*coords[i - 1], *coords[i])
            if pts.size > 0:
                small = pd.DataFrame(pts, columns=columns)
                if keep_columns:
                    for col in other_columns:
                        small[col] = replot_df.iloc[i][col]
                if fill_columns and keep_columns:
                    half = len(small) // 2
                    for col in other_columns:
                        small.loc[:half - 1, col] = replot_df.iloc[i - 1][col]
                        small.loc[half:, col] = replot_df.iloc[i][col]
                dfs.append(small)
    return pd.concat(dfs, ignore_index=True)


@pytest.mark.parametrize("keep, fill", [(False, False), (True, False), (True, True)])
def test_find_intermediate_points_matches_reference(keep, fill):
    rng = np.random.default_rng(1)
    df = pd.DataFrame(rng.integers(-20, 20, (40, 3)), columns=['X', 'Y', 'Z'])
    df['chain'] = ['A'] * 25 + ['B'] * 15
    df['atom'] = [f"A{i}" for i in range(40)]
    new = pdbm.find_intermediate_points(df, keep_columns=keep, fill_columns=fill)
    ref = reference_intermediate_points(df, keep_columns=keep, fill_columns=fill)
    if not keep:
        ref = ref[['X', 'Y', 'Z']]
    pd.testing.assert_frame_equal(new.reset_index(drop=True), ref, check_dtype=False)


def test_backbone_segments_break_at_gaps_and_chains():
    df = pd.DataFrame({'X': [0, 1.4, 2.9, 10, 11.4, 12.8], 'Y': 0.0, 'Z': 0.0,
                       'chain': ['A', 'A', 'A', 'A', 'A', 'B']})
    seg = pdbm.backbone_segments(df)
    assert seg[0] == seg[1] == seg[2]
    assert len({seg[2], seg[3], seg[5]}) == 3
    assert seg[3] == seg[4]
    # the same atoms scaled up stay connected when the threshold is scaled too
    scaled = df.assign(X=df['X'] * 3)
    assert list(pdbm.backbone_segments(scaled, scale=3)) == list(seg)


def test_polymer_mask_includes_modified_residues(write_pdb):
    text = (pdb_line("ATOM", 1, "N", "GLY", "A", 1, 0, 0, 0, "N")
            + pdb_line("HETATM", 2, "N", "MSE", "A", 2, 1, 0, 0, "N")
            + pdb_line("HETATM", 3, "CA", "MSE", "A", 2, 2, 0, 0, "C")
            + pdb_line("HETATM", 4, "C", "MSE", "A", 2, 3, 0, 0, "C")
            + pdb_line("HETATM", 5, "C1", "LIG", "A", 3, 9, 9, 9, "C"))
    df = pdbm.structure_to_df(StructureData.from_pdb(write_pdb(text)))
    assert list(pdbm.polymer_atom_mask(df)) == [True, True, True, True, False]


def test_secondary_structure_assignment_matches_row_by_row_lookup():
    s = StructureData.from_pdb(preset("Hemoglobin"))
    df = pdbm.structure_to_df(s)
    out = pdbm.add_structure_from_structured_data(df, s)
    info = s.structural_info
    expected = []
    for chain, resid in zip(df['chain'], df['resid']):
        hit = info[(info['chain'] == chain) & (info['resid1'] <= resid) & (info['resid2'] >= resid)]
        expected.append(hit['structure'].iloc[0] if len(hit) else "None")
    assert list(out['structure']) == expected


def test_hetatm_bond_lines():
    atoms = pd.DataFrame({'atom_num': [1, 2, 3], 'X': [0, 4, 9], 'Y': [0, 0, 0], 'Z': [0, 0, 0]})
    lines = pdbm.get_hetatm_bond_lines_from_df(atoms, [{'atom_num1': 1, 'atom_num2': 2},
                                                       {'atom_num1': 2, 'atom_num2': 99}])
    assert lines[['X', 'Y', 'Z']].values.tolist() == [[0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]]
    assert pdbm.get_hetatm_bond_lines_from_df(atoms, []).empty


def test_element_names_used_for_hetatm_colours():
    df = pd.DataFrame({'atom': ['CL', 'CA', 'C1', 'NA', 'O2'], 'element': ['CL', 'CA', 'C', 'NA', ''],
                       'row': 'HETATM'})
    assert list(pdbm.element_atom_names(df)['atom']) == ['CL', 'CA', 'C', 'NA', 'O']


def test_sphere_coordinates_are_integers():
    df = pd.DataFrame({'X': [0, 10], 'Y': [0, 0], 'Z': [0, 0], 'atom': ['C', 'O']})
    out = pdbm.add_sphere_coordinates(pdbm.rasterized_sphere(1.5), pdbm.sphere_center(1.5), df)
    assert all(out[c].dtype.kind == 'i' for c in 'XYZ')
    assert set(out['atom']) == {'C', 'O'}


def test_max_scale_uses_the_flattest_side():
    s = StructureData.from_pdb(preset("GFP"))
    df = pdbm.structure_to_df(s)
    height = (df[['X', 'Y', 'Z']].max() - df[['X', 'Y', 'Z']].min()).min()
    scale = pdbm.check_max_size(s, world_max=320)
    assert scale * height <= 320 < (scale + 0.1) * height
    assert pdbm.check_model_size(s, world_max=320)
    assert not pdbm.check_model_size(s, world_max=height - 1)


def test_load_structure_is_cached(tmp_path):
    path = tmp_path / "a.pdb"
    path.write_text(pdb_line("ATOM", 1, "CA", "GLY", "A", 1, 0, 0, 0, "C"))
    assert pdbm.load_structure(str(path)) is pdbm.load_structure(str(path))


def test_chain_numbers_cycle_one_to_ten():
    numbers = skeleton.chain_numbers([chr(65 + i) for i in range(12)])
    assert numbers['A'] == 1 and numbers['J'] == 10 and numbers['K'] == 1
