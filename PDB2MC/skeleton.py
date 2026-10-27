"""Skeleton mode: backbone, sidechain bonds and HETATM ball-and-stick."""
from PDB2MC.build import (  # noqa: F401  (re-exported for callers of the old skeleton API)
    BACKBONE_ATOMS, NOT_SIDECHAIN_ATOMS, ModelBuilder, backbone_blocks, chain_numbers, hetatm_blocks,
    prepare_coordinates, sidechain_blocks,
)


def build(builder):
    """Write <name>_backbone, _sidechain, _hetatm and _hetatm_bonds."""
    config = builder.config
    df = builder.df
    bonds = builder.structure.bonds
    builder.report(10)

    if config["backbone"]:
        builder.write(backbone_blocks(df, config, builder.numbers, bonds), "backbone")
    builder.report(40)

    if config["sidechain"]:
        builder.write(sidechain_blocks(df, config, builder.numbers), "sidechain")
    builder.report(70)

    if config["show_hetatm"]:
        spheres, bond_blocks = hetatm_blocks(df, builder.structure, config)
        builder.write(spheres, "hetatm")
        builder.write(bond_blocks, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, hetatom_df=None, hetatm_bonds=None, progress=None):
    """
    Generate the skeleton model structures (<name>_backbone, _sidechain, _hetatm, _hetatm_bonds).
    hetatom_df / hetatm_bonds are unused and kept for compatibility; HETATMs come from `structure`.
    `progress`, if given, is called with a percentage (0-100) of this step.
    """
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
