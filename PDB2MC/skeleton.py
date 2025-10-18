from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
import pandas as pd
from itertools import cycle
import re
import gc

def run_mode(config_data, pdb_name, structure, mc_dir, hetatom_df, hetatm_bonds):
    # Build main DataFrame from StructureData atoms
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
    # Annotate secondary structure
    df = pdbm.add_structure_from_structured_data(df, structure)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)

    # Backbone rendering
    if config_data["backbone"]:
        pdb_backbone = pdb_name + "_backbone"
        backbone = pdbm.atom_subset(df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                    ignore_het=True, include=True)
        if config_data["by_chain"]:
            by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
            chain_values = backbone["chain"].unique()
            for i, chain_value in enumerate(chain_values):
                chain_df = backbone[backbone["chain"] == chain_value]
                intermediate = pdbm.find_intermediate_points(chain_df)
                print("intermediated points: ", intermediate)
                intermediate = pdbm.cylinderize(intermediate, config_data["backbone_size"])
                intermediate["atom"] = (i + 1) if i < 10 else ((i + 1) % 10)
                by_chain_df = pd.concat([by_chain_df, intermediate], ignore_index=True)
            intermediate = by_chain_df
            del by_chain_df
        else:
            intermediate = pdbm.find_intermediate_points(backbone)
            intermediate = pdbm.cylinderize(intermediate, config_data["backbone_size"])
        print(intermediate.head())
        print(intermediate.tail())
        mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])
        del intermediate
        del backbone
        gc.collect()

    # Sidechain rendering
    if config_data["sidechain"]:
        by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
        sidechain = pdbm.atom_subset(df, ['N', 'P', "O5'", "C5'", "O3'"], ignore_het=True, include=False)
        chain_values = sidechain["chain"].unique()
        pdb_sidechain = pdb_name + "_sidechain"
        for i, chain_value in enumerate(chain_values):
            chain_df = sidechain[sidechain["chain"] == chain_value]

            print(chain_df.head())
            branches = pdbm.sidechain(chain_df)
            print(branches.head())
            if config_data["by_chain"]:
                branches["atom"] = (i + 1) if i < 10 else ((i + 1) % 10)
            else:
                branches['atom'] = 'sidechain_atom'
            by_chain_df = pd.concat([by_chain_df, branches], ignore_index=True)
        branches = by_chain_df
        mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # HETATM rendering
    if config_data["show_hetatm"]:
        hetatom_df_local = pdbm.filter_type_atom(df, remove_type="ATOM", remove_atom="H")
        hetatm_bonds_local = pdbm.get_hetatm_bond_lines_from_df(hetatom_df_local, structure.bonds)
        if hetatom_df_local is not None and not hetatom_df_local.empty:
            pdb_hetatm = pdb_name + "_hetatm"
            coord = pdbm.rasterized_sphere(config_data['atom_scale'])
            center = pdbm.sphere_center(config_data['atom_scale'])
            shortened = pdbm.shorten_atom_names(hetatom_df_local)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=False)
            spheres['atom'] = spheres['atom'].apply(lambda x: re.sub(r'P[A-Z]', 'P', x, count=1))
            mcf.create_nbt(spheres, pdb_hetatm, air=False, dir=mc_dir, blocks=config_data['atoms'])
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            if hetatm_bonds_local is not None and not hetatm_bonds_local.empty:
                mcf.create_nbt(hetatm_bonds_local, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])
