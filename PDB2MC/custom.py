"""Custom and X-Ray modes: atom spheres, backbone, sidechain bonds and HETATMs (X-Ray uses glass colours)."""
from PDB2MC.build import ModelBuilder, atom_spheres, backbone_blocks, hetatm_blocks, sidechain_blocks


def build(builder):
    """Write <name>_backbone, _sidechain, _atoms, _hetatm and _hetatm_bonds."""
    config = builder.config
    df = builder.df
    mesh = config.get('mesh', False)
    builder.report(5)

    if config["backbone"]:
        builder.write(backbone_blocks(df, config, builder.numbers, builder.structure.bonds), "backbone")
    builder.report(25)

    if config["sidechain"]:
        builder.write(sidechain_blocks(df, config, builder.numbers), "sidechain")
    builder.report(45)

    if config.get("show_atoms", True):
        builder.write(atom_spheres(df[df['row'] == 'ATOM'], config['atom_scale'], mesh=mesh), "atoms")
    builder.report(80)

    if config["show_hetatm"]:
        spheres, bonds = hetatm_blocks(df, builder.structure, config, mesh=mesh)
        builder.write(spheres, "hetatm")
        builder.write(bonds, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
