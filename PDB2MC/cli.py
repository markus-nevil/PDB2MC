"""
Build a model without the GUI:

    python -m PDB2MC.cli Skeleton path/to/model.pdb "C:/Users/me/AppData/Roaming/.minecraft/saves/My World"

Uses each mode's default settings and the metal ion blocks saved in the program; --scale, --by-chain,
--no-hetatm, --mesh, --name and --sasa-radius change the common ones.
"""
import argparse
import os
import sys

from PDB2MC import build, defaults, fetch, minecraft_functions as mcf, triggers, user_settings


def datapack_dir(world):
    """The datapack functions folder of a world (created, with pack.mcmeta, if missing)."""
    from shutil import copyfile
    from PDB2MC import resources
    functions = os.path.join(world, "datapacks", "mcPDB", "data", "protein", "functions")
    os.makedirs(functions, exist_ok=True)
    meta = os.path.join(world, "datapacks", "mcPDB", "pack.mcmeta")
    if not os.path.isfile(meta):
        copyfile(resources.package_file('pack.mcmeta'), meta)
    mcf.structure_dirs(functions)
    return functions


def main(argv=None):
    parser = argparse.ArgumentParser(description="Turn a PDB / mmCIF file into a Minecraft model.")
    parser.add_argument("mode", choices=defaults.MODES)
    parser.add_argument("structure", help=".pdb, .cif or .mmcif file, or a PDB ID such as 1GFL to download")
    parser.add_argument("world", help="Minecraft save folder (…/.minecraft/saves/<world>)")
    parser.add_argument("--scale", type=float, default=1.0)
    parser.add_argument("--by-chain", action="store_true", help="colour by chain")
    parser.add_argument("--no-hetatm", action="store_true", help="leave out other molecules")
    parser.add_argument("--mesh", action="store_true", help="mesh-style atoms / surface")
    parser.add_argument("--name", help="name of the model in Minecraft (default: the file name)")
    parser.add_argument("--sasa-radius", type=float, help="probe radius of Space Filling in angstroms")
    args = parser.parse_args(argv)
    if not os.path.exists(args.structure) and fetch.normalize_id(args.structure):
        print(f"Downloading {fetch.normalize_id(args.structure)}...")
        args.structure = fetch.download(args.structure)

    config = defaults.default_config(args.mode)
    config['atoms'].update(user_settings.metal_blocks())
    config.update(scale=args.scale, mesh=args.mesh, pdb_file=args.structure, save_path=datapack_dir(args.world),
                  model_name=args.name, triggers=True)
    if args.by_chain:
        config['by_chain'] = True
    if args.no_hetatm:
        config['show_hetatm'] = False
    if args.sasa_radius is not None:
        config['sasa_radius'] = args.sasa_radius
    name = build.build_model(args.mode, config, progress=lambda value: print(f"\r{value:3d}%", end=""))
    print(f"\nDone.\n{triggers.instructions(name, triggers.model_number(config['save_path'], name))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
