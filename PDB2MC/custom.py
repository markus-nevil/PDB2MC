from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
import pandas as pd
import re
from itertools import cycle

def run_mode(structure, config_data, pdb_name, mc_dir):
    # Convert StructureData atoms to DataFrame
    df = pd.DataFrame(structure.atoms)
    if 'x' in df.columns:
        df = df.rename(columns={'x': 'X', 'y': 'Y', 'z': 'Z'})
    if 'hetatm' in df.columns:
        df['row'] = df['hetatm'].apply(lambda h: 'HETATM' if h else 'ATOM')
    else:
        df['row'] = 'ATOM'
    if 'atom' in df.columns:
        df['atom'] = df['atom'].astype(str)
    df = pdbm.scale_coordinates(df, config_data['scale'])
    df = pdbm.move_coordinates(df)
    df = pdbm.rotate_to_y(df)
    df = pdbm.round_df(df)

    # Backbone
    if config_data["backbone"]:
        pdb_backbone = pdb_name + "_backbone"
        backbone = pdbm.atom_subset(df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"], include=True)
        if config_data["by_chain"]:
            by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
            chain_values = backbone["chain"].unique()
            for i, chain_value in enumerate(chain_values):
                chain_df = backbone[backbone["chain"] == chain_value]
                intermediate = pdbm.find_intermediate_points(chain_df)
                intermediate["atom"] = (i + 1) if i < 10 else ((i + 1) % 10)
                by_chain_df = pd.concat([by_chain_df, intermediate], ignore_index=True)
            intermediate = by_chain_df
        else:
            intermediate = pdbm.find_intermediate_points(backbone)
        cyl_diameter = float(config_data['backbone_size'])
        intermediate = pdbm.cylinderize(intermediate, cyl_diameter)
        mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # Sidechain
    if config_data["sidechain"]:
        if config_data["by_chain"]:
            cycle_sequence = cycle(range(1, 11))
            for chain, num in zip(enumerate(pdbm.enumerate_chains(df)), cycle_sequence):
                pdb_sidechain = pdb_name + "_" + chain[1] + "_sidechain"
                chain_df = pdbm.get_chain(df, chain[1])
                branches = pdbm.sidechain(chain_df)
                branches['atom'] = num
                mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])
        else:
            pdb_sidechain = pdb_name + "_sidechain"
            branches = pdbm.sidechain(df)
            branches['atom'] = 'sidechain_atom'
            mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # Atom spheres
    if config_data["show_atoms"]:
        pdb_atoms = pdb_name + "_atoms"
        if config_data['mesh'] and config_data['atom_scale'] < 2:
            coord = pdbm.rasterized_sphere(2)
            center = pdbm.sphere_center(2)
        else:
            coord = pdbm.rasterized_sphere(config_data['atom_scale'])
            center = pdbm.sphere_center(config_data['atom_scale'])
        atom_df = pdbm.filter_type_atom(df, remove_type="HETATM", remove_atom="H")
        shortened = pdbm.shorten_atom_names(atom_df)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
        mcf.create_nbt(spheres, pdb_atoms, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # HETATM
    if config_data["show_hetatm"]:
        hetatom_df = pdbm.filter_type_atom(df, remove_type="ATOM", remove_atom="H")
        hetatm_bonds = pdbm.get_hetatm_bond_lines_from_df(hetatom_df, getattr(structure, "bonds", None))
        if hetatom_df is not None and not hetatom_df.empty:
            pdb_hetatm = pdb_name + "_hetatm"
            if config_data['mesh'] and config_data['atom_scale'] < 2:
                coord = pdbm.rasterized_sphere(2)
                center = pdbm.sphere_center(2)
            else:
                coord = pdbm.rasterized_sphere(config_data['atom_scale'])
                center = pdbm.sphere_center(config_data['atom_scale'])
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
            spheres['atom'] = spheres['atom'].apply(lambda x: re.sub(r'P[A-Z]', 'P', x, count=1))
            mcf.create_nbt(spheres, pdb_hetatm, air=False, dir=mc_dir, blocks=config_data['atoms'])
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            if hetatm_bonds is not None and not hetatm_bonds.empty:
                mcf.create_nbt(hetatm_bonds, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])
