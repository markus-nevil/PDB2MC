import minecraft_functions as mcf
import pandas as pd
import numpy as np
import pdb_manipulation
import pdb_manipulation as pdbm
import variables as var
from itertools import cycle
import tifffile as tiff


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
            mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, "glowstone", replace=True)

            pdb_backbone = pdb_name + "_" + chain[1] + "_backbone"
            backbone = pdbm.atom_subset(space_filling_df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                        include=True)
            intermediate = pdbm.find_intermediate_points(backbone)
            intermediate['atom'] = num
            #mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
            #                               replace=False)
            mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, "glowstone",
                                           replace=False)

            pdb_atoms = pdb_name + "_" + chain[1] + "_atoms"

            #atom_chain_df = pdbm.get_chain(atom_df, chain[1])
            atom_chain_df = pdbm.get_chain(space_filling_df, chain[1])

            #make a new column with the atom type with column name 'atom_specific'
            atom_chain_df['atom_specific'] = atom_chain_df['atom']

            shortened = pdbm.shorten_atom_names(atom_chain_df)

            spheres = pd.DataFrame()
            #print(shortened.head(n=10))

            for value in shortened['atom_specific'].unique():
                print(value)
                #subset the dataframe by the atom type in 'value'
                atom_value_df = shortened[shortened['atom_specific'] == value]

                if value in var.radii:
                    radius_mod = 2.5 * var.radii[value]
                else:
                    radius_mod = 2.5
                #Check if the 'atom_specific' column contains 'C', 'CA', or 'N'
                #if 'C' in atom_value_df['atom_specific'].unique() or 'CA' in atom_value_df['atom_specific'].unique() or 'N' in atom_value_df['atom_specific'].unique() or 'O' in atom_value_df['atom_specific'].unique():
                #    radius_mod = radius_mod + 1
                coord = pdbm.rasterized_sphere(config_data['scale'] * radius_mod)
                center = pdbm.sphere_center(config_data['scale'] * radius_mod)
                spheres_temp = pdbm.add_sphere_coordinates(coord, center, atom_value_df, mesh=config_data['mesh'])
                spheres = pd.concat([spheres_temp, spheres], ignore_index=True)

                # Remove any rows with duplicate coordinates
                print(len(spheres))
                spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
                #print(spheres.head(n=10))


            spheres['atom'] = num
            print("And now I will take these and filter exterior:", len(spheres))
            surface_array = pdbm.construct_surface_array(spheres)
            surface_array = pdbm.paint_bucket_fill(surface_array)

            #create a path variable to the project directory in the ./docs folder
            array_path = mc_dir + "/" + pdb_name + "_" + chain[1] + "_array.tiff"
            #Create a copy of surface_array with the name surface_copy
            surface_copy = surface_array.copy()
            tiff_array = pdbm.preprocess_3d_array(surface_copy)
            tiff.imwrite(array_path, tiff_array)

            #save a single slice of the array (from the middle) as a text file
            slice_path = mc_dir + "/" + pdb_name + "_" + chain[1] + "_slice.txt"
            slice_array = surface_array[:, :, 50]
            np.savetxt(slice_path, slice_array, fmt='%d')

            print(spheres.tail(n=10))

            spheres = pdbm.filter_dataframe_by_fill_value(arr_3d=surface_array, df = spheres, fill_value=1e7)
            print("Exterior points: ", len(spheres))

            #Remove any rows with duplicate coordinates
            print(len(spheres))
            spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
            print(len(spheres))

            #spheres = pdbm.filter_exterior_points(spheres)
            #spheres = pd.merge(spheres_matrix[['X', 'Y', 'Z']], spheres, on=['X', 'Y', 'Z'], how='left')

            #backbone = pdbm.atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
            #                            include=True)
            #combined = pd.concat([backbone, pdbm.sidechain(space_filling_df)])
            #remove = pdbm.cylinderize(combined, config_data['scale']-1)

            #merged = spheres.merge(remove, on=['X', 'Y', 'Z'], how='outer', indicator=True)
            #print(merged.head(n=10))
            #spheres = merged[merged['_merge'] == 'left_only'].drop(columns='_merge')
            #print(len(spheres))

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
                radius_mod = 2 * var.radii[value]
            else:
                radius_mod = 2
            print(value, ": ", radius_mod)
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
            coord = pdbm.rasterized_sphere(config_data['scale'])
            center = pdbm.sphere_center(config_data['scale'])
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
            mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'], replace=False)
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
