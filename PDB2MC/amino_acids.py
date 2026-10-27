"""Amino Acids mode: one hollow sphere per residue, coloured by residue type, on the backbone."""
import numpy as np
import pandas as pd

from PDB2MC import pdb_manipulation as pdbm
from PDB2MC.build import ModelBuilder, backbone_blocks, hetatm_blocks

# Nucleotides get fixed colours
DNA_BASES = {
    "DA": "lime_concrete",
    "DC": "blue_concrete",
    "DG": "black_concrete",
    "DT": "red_concrete",
    "A": "lime_wool",
    "C": "blue_wool",
    "G": "black_wool",
    "T": "red_wool",
    "U": "red_wool",
}

# Residues are placed at their alpha carbon (protein) or C4' (nucleic acid)
RESIDUE_CENTRE_ATOMS = ['CA', "C4'"]


def shell_offsets(radius):
    """Offsets of the outer layer of a rasterised sphere (its 26-connected border)."""
    sphere = pdbm.rasterized_sphere(radius).astype(np.uint8) * 255
    shell = pdbm.find_border_cells(sphere)
    return np.argwhere(shell > 0) - np.array(pdbm.sphere_center(radius))


def filled_offsets(radius):
    return np.argwhere(pdbm.rasterized_sphere(radius) > 0) - np.array(pdbm.sphere_center(radius))


def place(offsets, centres, labels):
    """Copy `offsets` around every centre; each copy gets that centre's label."""
    coords = (centres[:, None, :] + offsets[None, :, :]).reshape(-1, 3)
    blocks = pd.DataFrame(coords.astype(int), columns=['X', 'Y', 'Z'])
    blocks['atom'] = np.repeat(np.asarray(labels, dtype=object), len(offsets))
    return blocks


def without(blocks, occupied):
    """Rows of blocks whose position is not in occupied (both DataFrames with X, Y, Z)."""
    if blocks.empty or occupied.empty:
        return blocks
    keys = pd.MultiIndex.from_frame(blocks[['X', 'Y', 'Z']].astype(int))
    taken = pd.MultiIndex.from_frame(occupied[['X', 'Y', 'Z']].astype(int))
    return blocks[~keys.isin(taken)]


def residue_centres(df):
    """One row per polymer residue at its CA / C4' atom."""
    centres = df[df['polymer'] & df['atom'].isin(RESIDUE_CENTRE_ATOMS)]
    return centres.drop_duplicates(subset=['chain', 'resid'])


def build(builder):
    """Write <name>_atoms (residue spheres), _backbone, _hetatm and _hetatm_bonds."""
    config = builder.config
    df = builder.df
    radius = config['atom_scale']
    centres = residue_centres(df)
    centre_xyz = centres[['X', 'Y', 'Z']].to_numpy(dtype=int)
    colours = {**config.get('amino_acids', {}), **DNA_BASES,
               'other_atom': config['atoms'].get('other_atom', 'pink_concrete')}
    builder.report(10)

    spheres = place(shell_offsets(radius), centre_xyz, centres['residue'].to_numpy())
    builder.write(spheres, "atoms", atoms=centres, block_lookup=colours)
    builder.report(50)

    if config["backbone"]:
        backbone = backbone_blocks(df, config, builder.numbers, builder.structure.bonds)
        # The backbone inside a residue sphere is hidden anyway; leaving it out saves blocks
        backbone = without(backbone, place(filled_offsets(radius), centre_xyz, np.zeros(len(centres))))
        builder.write(backbone, "backbone")
    builder.report(75)

    if config["show_hetatm"]:
        spheres, bonds = hetatm_blocks(df, builder.structure, config)
        builder.write(spheres, "hetatm")
        builder.write(bonds, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
