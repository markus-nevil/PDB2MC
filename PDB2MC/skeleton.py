from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
import pandas as pd
import gc

# Atoms joined into the backbone line: protein N-CA-C and the nucleic acid sugar-phosphate chain
BACKBONE_ATOMS = ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"]
# Backbone atoms left out of the sidechain bond search (CA, C and C4'/C3' anchor the branches)
NOT_SIDECHAIN_ATOMS = ['N', 'P', "O5'", "C5'", "O3'"]


def chain_numbers(chains):
    """Colour number 1-10 for each chain, in order of first appearance (cycling after ten chains)."""
    return {chain: (i % 10) + 1 for i, chain in enumerate(pd.unique(pd.Series(chains)))}


def prepare_coordinates(structure, scale):
    """
    Scaled, origin-shifted, Y-rotated and rounded coordinates for a StructureData, with extra columns:
    'polymer' (protein/nucleic acid atom, including modified HETATM residues) and 'segment' (continuous
    backbone stretch id for backbone atoms, None elsewhere). Waters are removed.
    """
    df = pdbm.structure_to_df(structure)
    if df.empty:
        raise ValueError("The structure contains no atoms.")
    df = pdbm.scale_coordinates(df, scale)
    df = pdbm.move_coordinates(df)
    df = pdbm.rotate_to_y(df)

    # Chain breaks are found on the unrounded coordinates; rounding would blur bond lengths
    df['polymer'] = pdbm.polymer_atom_mask(df)
    backbone_mask = (df['polymer'] & df['atom'].isin(BACKBONE_ATOMS)).to_numpy()
    segment = pd.Series(None, index=df.index, dtype=object)
    segment[backbone_mask] = pdbm.backbone_segments(df[backbone_mask], scale=scale)
    df['segment'] = segment
    return pdbm.round_df(df).reset_index(drop=True)


def backbone_blocks(df, config_data, numbers):
    """Cylinder blocks along every continuous backbone segment."""
    backbone = df[df['segment'].notna()]
    if backbone.empty:
        return pd.DataFrame(columns=['X', 'Y', 'Z'])
    parts = []
    groups = backbone.groupby('chain', sort=False) if config_data["by_chain"] else [(None, backbone)]
    for chain, chain_df in groups:
        # Connect points only within a segment: find_intermediate_points joins rows with equal 'chain'
        line = pdbm.find_intermediate_points(chain_df[['X', 'Y', 'Z']].assign(chain=chain_df['segment']))
        if line.empty:
            continue
        cylinder = pdbm.cylinderize(line.copy(), config_data["backbone_size"])
        if chain is not None:
            cylinder['atom'] = numbers[chain]
        parts.append(cylinder)
    if not parts:
        return pd.DataFrame(columns=['X', 'Y', 'Z'])
    return pd.concat(parts, ignore_index=True)


def sidechain_blocks(df, config_data, numbers):
    """Lines along every sidechain bond from chains.txt."""
    side = df[df['polymer'] & ~df['atom'].isin(NOT_SIDECHAIN_ATOMS)]
    if side.empty:
        return pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
    if not config_data["by_chain"]:
        branches = pdbm.sidechain(side)
        branches['atom'] = 'sidechain_atom'
        return branches
    parts = []
    for chain, chain_df in side.groupby('chain', sort=False):
        branches = pdbm.sidechain(chain_df)
        branches['atom'] = numbers[chain]
        parts.append(branches)
    return pd.concat(parts, ignore_index=True).drop_duplicates()


def hetatm_blocks(df, structure, config_data):
    """Spheres coloured by element for HETATM atoms, and lines for their bonds."""
    het = df[df['row'] == 'HETATM'].reset_index(drop=True)
    if het.empty:
        return None, None
    coord = pdbm.rasterized_sphere(config_data['atom_scale'])
    center = pdbm.sphere_center(config_data['atom_scale'])
    spheres = pdbm.add_sphere_coordinates(coord, center, pdbm.element_atom_names(het), mesh=False)
    bonds = pdbm.get_hetatm_bond_lines_from_df(het, structure.bonds)
    return spheres, bonds


def run_mode(config_data, pdb_name, structure, mc_dir, hetatom_df=None, hetatm_bonds=None, progress=None):
    """
    Generate the skeleton model structures (<name>_backbone, _sidechain, _hetatm, _hetatm_bonds).
    hetatom_df / hetatm_bonds are unused and kept for compatibility; HETATMs come from `structure`.
    `progress`, if given, is called with a percentage (0-100) of this step.
    """
    report = progress or (lambda value: None)
    df = prepare_coordinates(structure, config_data['scale'])
    numbers = chain_numbers(df.loc[df['polymer'], 'chain'])
    blocks = config_data['atoms']
    report(10)

    # Backbone rendering
    if config_data["backbone"]:
        mcf.create_nbt(backbone_blocks(df, config_data, numbers), pdb_name + "_backbone",
                       air=False, dir=mc_dir, blocks=blocks)
        gc.collect()
    report(40)

    # Sidechain rendering
    if config_data["sidechain"]:
        mcf.create_nbt(sidechain_blocks(df, config_data, numbers), pdb_name + "_sidechain",
                       air=False, dir=mc_dir, blocks=blocks)
    report(70)

    # HETATM rendering
    if config_data["show_hetatm"]:
        spheres, bonds = hetatm_blocks(df, structure, config_data)
        if spheres is not None and not spheres.empty:
            mcf.create_nbt(spheres, pdb_name + "_hetatm", air=False, dir=mc_dir, blocks=blocks)
        if bonds is not None and not bonds.empty:
            mcf.create_nbt(bonds, pdb_name + "_hetatm_bonds", air=False, dir=mc_dir, blocks=blocks)
    report(100)
