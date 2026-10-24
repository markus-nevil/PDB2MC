import glob
import os

import pytest

from PDB2MC.structure_data import StructureData, minecraft_name
from conftest import pdb_line, PRESETS, preset


def test_alternate_locations_keep_one_conformer(write_pdb):
    text = (pdb_line("ATOM", 1, "N", "SER", "A", 1, 0, 0, 0, "N")
            + pdb_line("ATOM", 2, "CA", "SER", "A", 1, 1.5, 0, 0, "C", altloc="A")
            + pdb_line("ATOM", 3, "CA", "SER", "A", 1, 1.6, 0.2, 0, "C", altloc="B")
            + pdb_line("ATOM", 4, "OG", "SER", "A", 1, 2, 1, 0, "O", altloc="A")
            + pdb_line("ATOM", 5, "OG", "SER", "A", 1, 2, -1, 0, "O", altloc="B"))
    s = StructureData.from_pdb(write_pdb(text))
    assert [a['atom_num'] for a in s.atoms] == [1, 2, 4]


def test_only_first_model_is_read(write_pdb):
    model = pdb_line("ATOM", 1, "CA", "GLY", "A", 1, 0, 0, 0, "C")
    text = "MODEL        1\n" + model + "ENDMDL\nMODEL        2\n" + model + "ENDMDL\nEND\n"
    s = StructureData.from_pdb(write_pdb(text))
    assert len(s.atoms) == 1


def test_hydrogens_dropped_by_element_but_mercury_kept(write_pdb):
    text = (pdb_line("ATOM", 1, "CA", "GLY", "A", 1, 0, 0, 0, "C")
            + pdb_line("ATOM", 2, "HA2", "GLY", "A", 1, 1, 0, 0, "H")
            + pdb_line("ATOM", 3, "HA3", "GLY", "A", 1, 1, 1, 0, "D")
            + pdb_line("HETATM", 4, "HG", "HG", "A", 101, 5, 5, 5, "HG"))
    s = StructureData.from_pdb(write_pdb(text))
    assert [(a['atom'], a['element']) for a in s.atoms] == [("CA", "C"), ("HG", "HG")]


def test_element_inferred_when_columns_missing(write_pdb):
    lines = [pdb_line("ATOM", 1, "CA", "GLY", "A", 1, 0, 0, 0)[:66] + "\n",
             pdb_line("HETATM", 2, "FE", "HEM", "A", 2, 0, 0, 0)[:66].replace(" FE ", "FE  ") + "\n",
             pdb_line("ATOM", 3, "HG21", "THR", "A", 3, 0, 0, 0)[:66] + "\n"]
    s = StructureData.from_pdb(write_pdb("".join(lines)))
    assert [a['element'] for a in s.atoms] == ["C", "FE"]   # HG21 is a hydrogen


def test_conect_bonds_deduplicated_and_hetatm_only(write_pdb):
    text = (pdb_line("ATOM", 1, "C", "GLY", "A", 1, 0, 0, 0, "C")
            + pdb_line("ATOM", 2, "O", "GLY", "A", 1, 1, 0, 0, "O")
            + pdb_line("HETATM", 3, "C1", "LIG", "A", 2, 5, 0, 0, "C")
            + pdb_line("HETATM", 4, "O1", "LIG", "A", 2, 6, 0, 0, "O")
            + "CONECT    1    2\nCONECT    3    4\nCONECT    4    3\nCONECT    1    3\n")
    s = StructureData.from_pdb(write_pdb(text))
    pairs = sorted(tuple(sorted(b.values())) for b in s.bonds)
    assert pairs == [(1, 3), (3, 4)]   # ATOM-ATOM bond 1-2 skipped, 3-4 listed twice kept once


def test_secondary_structure_and_metadata():
    s = StructureData.from_pdb(preset("Hemoglobin"))
    assert s.metadata['id'] == "3BJ1"
    assert not s.structural_info.empty
    assert set(s.structural_info['structure']) <= {"helix", "sheet"}
    assert s.structural_info['resid1'].dtype.kind == "i"
    assert s.chain_identity  # COMPND chain names


def test_names_come_from_the_file_name():
    # Both presets carry HEADER id 3BJ1; their generated files must not overwrite each other
    assert StructureData.from_pdb(preset("Helix")).name == "helix"
    assert StructureData.from_pdb(preset("Hemoglobin")).name == "hemoglobin"


@pytest.mark.parametrize("text, expected", [
    ("1ABC", "1abc"),
    ("AF-P69905-F1-model_v4", "af-p69905-f1-model_v4"),
    ("my protein (final)", "my_protein_final"),
    ("???", "model"),
])
def test_minecraft_name(text, expected):
    assert minecraft_name(text) == expected


@pytest.mark.parametrize("path", sorted(glob.glob(os.path.join(PRESETS, "*.pdb"))), ids=os.path.basename)
def test_every_preset_parses(path):
    s = StructureData.from_file(path)
    assert s.atoms
    assert all(a['element'] not in ("H", "D") for a in s.atoms)


MMCIF = """data_TEST
_entry.id TEST
_struct.title 'Test structure'
loop_
_entity.id
_entity.pdbx_description
1 'Test protein'
2 'ZINC ION'
loop_
_entity_poly.entity_id
_entity_poly.pdbx_strand_id
1 A
loop_
_struct_conf.conf_type_id
_struct_conf.beg_auth_asym_id
_struct_conf.beg_auth_comp_id
_struct_conf.beg_auth_seq_id
_struct_conf.end_auth_asym_id
_struct_conf.end_auth_comp_id
_struct_conf.end_auth_seq_id
HELX_P A GLY 1 A ALA 2
loop_
_chem_comp_bond.comp_id
_chem_comp_bond.atom_id_1
_chem_comp_bond.atom_id_2
LIG C1 O1
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.auth_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.auth_asym_id
_atom_site.pdbx_PDB_model_num
ATOM 1 N N . GLY A 1 ? 0.0 0.0 0.0 A 1
ATOM 2 C CA A GLY A 1 ? 1.4 0.0 0.0 A 1
ATOM 3 C CA B GLY A 1 ? 1.5 0.1 0.0 A 1
ATOM 4 H H . GLY A 1 ? 0.0 1.0 0.0 A 1
ATOM 5 C CA . ALA A 2 ? 3.8 0.0 0.0 A 1
HETATM 6 C C1 . LIG B 10 ? 8.0 0.0 0.0 A 1
HETATM 7 O O1 . LIG B 10 ? 9.2 0.0 0.0 A 1
HETATM 8 HG HG . HG C 11 ? 9.2 3.0 0.0 A 1
ATOM 9 N N . GLY A 1 ? 0.0 0.0 5.0 A 2
"""


def test_mmcif_parsing(tmp_path):
    path = tmp_path / "test.cif"
    path.write_text(MMCIF)
    s = StructureData.from_file(str(path))
    assert [a['atom_num'] for a in s.atoms] == [1, 2, 5, 6, 7, 8]   # altloc B, hydrogen, model 2 dropped
    assert s.atoms[-1]['element'] == "HG"
    assert s.bonds == [{'atom_num1': 6, 'atom_num2': 7}]
    assert s.chain_identity == {"A": "Test protein"}
    assert s.structural_info.iloc[0].tolist() == ["A", "GLY", 1, "ALA", 2, "helix"]
    assert s.metadata['id'] == "TEST" and s.name == "test"
    assert [code for _, code in s.sequences["A"]] == ["G", "A"]
