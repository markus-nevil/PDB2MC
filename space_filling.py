import minecraft_functions as mcf
import pandas as pd
import pdb_manipulation as pdbm
import variables as var
from itertools import cycle


def run_mode(config_data, pdb_name, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):

    if config_data["by_chain"]:
        # Create a cycle from 1 to 10 to aid in chain coloring
        cycle_sequence = cycle(range(1, 11))

        space_filling_master_df = rounded

        # Iterate through each chain and count the number of loops
        for chain, num in zip(enumerate(pdbm.enumerate_chains(space_filling_master_df)), cycle_sequence):
            pdb_sidechain = pdb_name + "_" + chain[1] + "_sidechain"
            space_filling_df = pdbm.get_chain(space_filling_master_df, chain[1])
            branches = pdbm.sidechain(space_filling_df)
            branches['atom'] = num
            mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'], replace=True)

            pdb_atoms = pdb_name + "_" + chain[1] + "_atoms"

            atom_chain_df = pdbm.get_chain(atom_df, chain[1])
            shortened = pdbm.shorten_atom_names(atom_chain_df)

            spheres = pd.DataFrame()
            for value in shortened['atom'].unique():
                if value in var.radii:
                    radius_mod = 1.5 * var.radii[value]
                else:
                    radius_mod = 1.5
                coord = pdbm.rasterized_sphere(config_data['scale'] * radius_mod)
                center = pdbm.sphere_center(config_data['scale'] * radius_mod)
                spheres_temp = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                spheres = pd.concat([spheres_temp, spheres], ignore_index=True)
                # Remove any rows with duplicate coordinates
                spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')

            spheres['atom'] = num

            #Remove any rows with duplicate coordinates
            spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')

            mcf.create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'], replace=False)

    else:
        branches = pdbm.sidechain(rounded)

        pdb_sidechain = pdb_name + "_sidechain"

        mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'], replace=True)

        pdb_atoms = pdb_name + "_atoms"

        shortened = pdbm.shorten_atom_names(atom_df)

        spheres = pd.DataFrame()
        for value in shortened['atom'].unique():

            if value in var.radii:
                radius_mod = 1.5*var.radii[value]
            else:
                radius_mod = 1.5
            coord = pdbm.rasterized_sphere(config_data['scale']*radius_mod)
            center = pdbm.sphere_center(config_data['scale']*radius_mod)
            spheres_temp = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
            spheres = pd.concat([spheres_temp, spheres], ignore_index=True)

        # Remove any rows with duplicate coordinates
        spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')

        mcf.create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'], replace=False)

    if config_data["show_hetatm"]:
        if hetatom_df is not None:
            pdb_hetatm = pdb_name + "_hetatm"
            coord = pdbm.rasterized_sphere(config_data['scale']*1.5)
            center = pdbm.sphere_center(config_data['scale']*1.5)
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
            mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'], replace=False)
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
