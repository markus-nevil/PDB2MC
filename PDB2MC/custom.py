"""Custom and X-Ray modes: atom spheres, backbone, sidechain bonds and HETATMs (X-Ray uses glass colours)."""
from PDB2MC.build import ModelBuilder, atom_spheres, backbone_blocks, hetatm_blocks, part_work, sidechain_blocks


def build(builder):
    """Write <name>_backbone, _sidechain, _atoms, _hetatm and _hetatm_bonds."""
    config = builder.config
    df = builder.df
    mesh = config.get('mesh', False)
    builder.plan(part_work(df, config))

    if config["backbone"]:
        builder.step("backbone", "Drawing the backbone...")
        builder.write(backbone_blocks(df, config, builder.numbers, builder.structure.bonds), "backbone")

    if config["sidechain"]:
        builder.step("sidechain", "Drawing the side chains...")
        builder.write(sidechain_blocks(df, config, builder.numbers), "sidechain")

    if config.get("show_atoms", True):
        builder.step("atoms", "Placing the atoms...")
        builder.write(atom_spheres(df[df['row'] == 'ATOM'], config['atom_scale'], mesh=mesh), "atoms")

    if config["show_hetatm"]:
        builder.step("hetatm", "Placing the other molecules...")
        spheres, bonds = hetatm_blocks(df, builder.structure, config, mesh=mesh)
        builder.write(spheres, "hetatm")
        builder.step("hetatm_bonds")
        builder.write(bonds, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
