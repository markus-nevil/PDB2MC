import minecraft_functions as mcf
import pandas as pd
import numpy as np
import pdb_manipulation
import pdb_manipulation as pdbm
import variables as var
from itertools import cycle
from datetime import datetime
import tifffile as tiff

def run_mode(config_data, pdb_name, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):
    x = False

    if not x:
        # Create a cycle from 1 to 10 to aid in chain coloring
        cycle_sequence = cycle(range(1, 11))
        space_filling_master_df = rounded
        space_filling_total_df = pd.DataFrame()
        point_df = pd.DataFrame()
        atoms_only_df = pd.DataFrame()

        # Iterate through each chain and count the number of loops
        for chain, num in zip(enumerate(pdbm.enumerate_chains(space_filling_master_df)), cycle_sequence):
            #print("chain: ", chain)
            space_filling_df = pdbm.get_chain(space_filling_master_df, chain[1])

            if config_data["by_chain"]:
                # Subset just the X, Y, Z columns and make a new dataframe called atoms_subset_df
                atoms_subset_df = space_filling_df[['X', 'Y', 'Z']]
                # Add a new column called 'atom' and fill it with the values of num
                atoms_subset_df['atom'] = num
            else:
                atoms_subset_df = space_filling_df[['X', 'Y', 'Z', 'atom']]
                #Take only the first character from the 'atom' column
                atoms_subset_df['atom'] = atoms_subset_df['atom'].str[0]

            branches = pdbm.sidechain(space_filling_df)
            #branches['atom'] = "branches"
            branches['atom'] = num
            backbone = pdbm.atom_subset(space_filling_df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                        include=True)
            intermediate = pdbm.find_intermediate_points(backbone)

            #intermediate['atom'] = "backbone"
            intermediate['atom'] = num
            point_list = [branches, intermediate, point_df]
            point_df = pd.concat(point_list, ignore_index=True)

            atom_list = [atoms_only_df, atoms_subset_df]
            atoms_only_df = pd.concat(atom_list, ignore_index=True)

        shortened = pdbm.shorten_atom_names(space_filling_master_df)

        coord = pdbm.rasterized_sphere(round(config_data['scale'] * .9))
        center = pdbm.sphere_center(round(config_data['scale'] * .9))
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])

        # Remove any rows with duplicate coordinates
        spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
        spheres['atom'] = 'atom'

        all_points = pd.concat([spheres, point_df], ignore_index=True)
        point_np = pdbm.construct_surface_array_by_type(all_points, include=['atom', 'backbone', 'branches'])

        bool_array = pdbm.SASA_gaussian_surface(point_np, sigma=config_data['scale'] / 1.5, fill=True)

        #Reverse 0 and 255 values of bool_array
        #bool_array = np.where(bool_array == 0, 255, 0)
        # Make all values >= 1 equal 255
        bool_array = np.where(bool_array >= 1, 255, 0)
        bool_array = bool_array.astype(np.uint8)

        #bool_df = pdbm.array_to_voxel(bool_array)
        #bool_df['atom'] = 10

        pdbm.save_3d_tiff(bool_array, r'C:\Users\marku\Desktop\point_np.tif')

        master_bool = pdbm.find_border_cells(bool_array)

        # convert all values to uint8 with a max of 255
        master_bool = master_bool.astype(np.uint8)

        pdbm.save_3d_tiff(master_bool, r'C:\Users\marku\Desktop\master_bool_array.tif')

        master_array = pdbm.array_to_voxel(master_bool, padding_size=0)

        test_check = pdbm.construct_surface_array(master_array)
        pdbm.save_3d_tiff(test_check, r'C:\Users\marku\Desktop\test_check.tif')
        master_array['atom'] = 0

        if hetatom_df is not None:
            aligned_dfs = pdbm.align_dataframes(master_array, point_df, atoms_only_df, hetatom_df, hetatm_bonds)
            master_array = aligned_dfs[0]
            point_df = aligned_dfs[1]
            atoms_subset_df = aligned_dfs[2]
            aligned_hetatm = aligned_dfs[3]
            aligned_hetatm_bonds = aligned_dfs[4]
        else:
            aligned_dfs = pdbm.align_dataframes(master_array, point_df, atoms_only_df)
            master_array = aligned_dfs[0]
            point_df = aligned_dfs[1]
            atoms_subset_df = aligned_dfs[2]

        if config_data['mesh'] == True:
            master_array = pdbm.remove_random_rows(master_array, percent = 90)

        output_df = pdbm.assign_atom_values(master_array, atoms_subset_df)

        pdb_surface = pdb_name + "_surface"
        pdb_branch = pdb_name + "_branch"

        #Add a 'b' to the end of the values in the 'atom' column of point_df
        point_df['atom'] = point_df['atom'].astype(str) + 'b'

        mcf.create_minecraft_functions(point_df, pdb_surface, False, mc_dir, config_data['atoms'], replace=True)
        mcf.create_minecraft_functions(output_df, pdb_branch, False, mc_dir, config_data['atoms'], replace=True)

        if config_data["show_hetatm"]:
            if hetatom_df is not None:

                #pdb_hetatm, hetatm_bonds = pdbm.adjust_hetatm_coordinates(space_filling_df, output_df, hetatom_df, hetatm_bonds)
                pdb_hetatm = pdb_name + "_hetatm"
                scale = round(config_data['scale'] - 1)
                coord = pdbm.rasterized_sphere(scale)
                center = pdbm.sphere_center(scale)
                shortened = pdbm.shorten_atom_names(aligned_hetatm)
                spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'], replace=False)
                pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"

                # Easiest way to ensure bonds are grey concrete
                hetatm_bonds['atom'] = 99
                mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])



    if config_data["by_chain"] and x:
        # Create a cycle from 1 to 10 to aid in chain coloring
        cycle_sequence = cycle(range(1, 11))

        space_filling_master_df = rounded

        #make an empty df to hold all the chains
        space_filling_total_df = pd.DataFrame()

        # Iterate through each chain and count the number of loops
        for chain, num in zip(enumerate(pdbm.enumerate_chains(space_filling_master_df)), cycle_sequence):
            pdb_sidechain = pdb_name + "_" + chain[1] + "_sidechain"
            space_filling_df = pdbm.get_chain(space_filling_master_df, chain[1])
            branches = pdbm.sidechain(space_filling_df)
            branches['atom'] = "branches"
            pdb_backbone = pdb_name + "_" + chain[1] + "_backbone"
            backbone = pdbm.atom_subset(space_filling_df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                        include=True)
            intermediate = pdbm.find_intermediate_points(backbone)
            intermediate['atom'] = "backbone"
            # mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, "glowstone",
            #                                replace=False)
            # intermediate_surface = pdbm.construct_surface_array(intermediate)
            # intermediate_padded = np.pad(intermediate_surface, 0, mode='constant', constant_values=0)
            # pdbm.save_3d_tiff(intermediate_padded, r'C:\Users\marku\Desktop\pdb_intermediate_padded_array.tif')

            pdb_atoms = pdb_name + "_" + chain[1] + "_atoms"

            atom_chain_df = pdbm.get_chain(atom_df, chain[1])
            shortened = pdbm.shorten_atom_names(atom_chain_df)

            coord = pdbm.rasterized_sphere(round(config_data['scale'] * .9))
            center = pdbm.sphere_center(round(config_data['scale'] * .9))
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])

            # Remove any rows with duplicate coordinates
            spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
            spheres['atom'] = num

            point_list = [spheres, branches, intermediate]
            point_df = pd.concat(point_list, ignore_index=True)
            point_np = pdbm.construct_surface_array_by_type(point_df, include=['backbone', 'branches'])
            print("point_np: ", point_np.shape)
            point_shape = point_np.shape
            point_np = np.pad(point_np, 30, mode='constant', constant_values=0)
            print("point_np after padding: ", point_np.shape)
            #pdbm.save_3d_tiff(point_np, r'C:\Users\marku\Desktop\point_np.tif')


            bonds = pdbm.array_to_voxel(point_np)
            bonds['atom'] = num
            mcf.create_minecraft_functions(bonds, pdb_backbone, False, mc_dir, config_data['atoms'], replace=True)
            #mcf.create_minecraft_functions(bonds, pdb_backbone, False, mc_dir, "glowstone", replace=True)
            print("points: ", point_np.shape)


            surface_array = pdbm.construct_surface_array(spheres)
            bool_array = pdbm.SASA_gaussian_surface(surface_array, sigma=config_data['scale']/1.5, fill=True)
            bool_df = pdbm.array_to_voxel(bool_array)
            print("bool ar ray after SASA is: ", bool_array.shape)
            bool_df['atom'] = num
            #bool_surface = pdbm.construct_surface_array(bool_array)
            #bool_surface = np.pad(bool_surface, 30, mode='constant', constant_values=0)
            #print("boolean: ", bool_surface.shape)
            #surface_padded = np.pad(surface_array, 20, mode='constant', constant_values=0)
            #bool_array = pdbm.contour_outline(surface_array)

            # Save your 3D NumPy array as a 3D TIFF image
            pdbm.save_3d_tiff(bool_array, r'C:\Users\marku\Desktop\pdb_output_array.tif')

            pdbm.save_3d_tiff(point_np, r'C:\Users\marku\Desktop\pdb_padded_array.tif')

### TODO this might need to come back
            #surface_filtered_array = pdbm.filter_3d_array_with_bool(surface_array, bool_array)

            #spheres = pdbm.filter_dataframe_by_array(df=spheres, arr_3d=surface_filtered_array)

            #Remove any rows with duplicate coordinates
            #spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
###
            #blurred = pdbm.blur_3d_array(surface_array, 1.25)
            # Save your 3D NumPy array as a 3D TIFF image
            #output_path = r'C:\Users\marku\Desktop\pdb_blurred_array.tif'  # Path where you want to save the TIFF image
            #pdbm.save_3d_tiff(blurred, output_path)

            #blurred_bool = pdbm.contour_outline(blurred)
            # Save your 3D NumPy array as a 3D TIFF image
            #output_path = r'C:\Users\marku\Desktop\pdb_blurred_bool.tif'  # Path where you want to save the TIFF image
            #pdbm.save_3d_tiff(blurred_bool, output_path)

            #output_df = pdbm.array_to_voxel(blurred_bool, atom=num)
            #mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, "glowstone", replace=True)

            ##Individual
            #mcf.create_minecraft_functions(bool_df, pdb_atoms, False, mc_dir, config_data['atoms'], replace=False)

            #mcf.create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'], replace=False)
            #mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, "glowstone", replace=False)

            #add spheres to the master df
            space_filling_total_df = pd.concat([space_filling_total_df, bool_df], ignore_index=True)
            #remove duplicates that match x, y, z but keep all columns
            space_filling_total_df = space_filling_total_df.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
            print("space fill df: ", len(space_filling_total_df))

        if config_data["show_hetatm"]:
            if hetatom_df is not None:

                pdb_hetatm, hetatm_bonds = pdbm.adjust_hetatm_coordinates(space_filling_df, bool_df, hetatom_df, hetatm_bonds)
                pdb_hetatm = pdb_name + "_hetatm"
                scale = round(config_data['scale'] - 1)
                coord = pdbm.rasterized_sphere(scale)
                center = pdbm.sphere_center(scale)
                shortened = pdbm.shorten_atom_names(hetatom_df)
                spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'], replace=False)
                pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"

                # Easiest way to ensure bonds are grey concrete
                hetatm_bonds['atom'] = 99
                mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])

        master_surface = pdbm.construct_surface_array(space_filling_total_df)
        pdbm.save_3d_tiff(master_surface,  r'C:\Users\marku\Desktop\pdb_surface_master_array.tif')

        #Make the master_bool have 0 = 255 and anything >= 1 to 0
        #master_bool = pdbm.contour_outline(master_surface, fill=True)
        master_bool = pdbm.find_border_cells(master_surface)
        pdbm.save_3d_tiff(master_bool, r'C:\Users\marku\Desktop\master_bool_array.tif')
        #master_bool = pdbm.contour_outline(master_bool, fill=False)

        #master_bool_df = pdbm.filter_df_with_array(space_filling_total_df, master_bool)
        master_bool_df = pdbm.align_and_filter_dataframes(numpy_array=master_bool, original_df=space_filling_total_df)
        mcf.create_minecraft_functions(master_bool_df,pdb_atoms, False, mc_dir, config_data['atoms'], replace=False)
        pdbm.save_3d_tiff(master_bool,  r'C:\Users\marku\Desktop\pdb_contour_master_array.tif')

    #else:
    elif x == 1000:
        branches = pdbm.sidechain(rounded)

        pdb_sidechain = pdb_name + "_sidechain"

        mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, "glowstone", replace=True)

        pdb_backbone = pdb_name + "_" + "_backbone"
        backbone = pdbm.atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                    include=True)
        intermediate = pdbm.find_intermediate_points(backbone)
        intermediate['atom'] = 1
        mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, "glowstone",
                                       replace=False)

        pdb_atoms = pdb_name + "_atoms"

        shortened = pdbm.shorten_atom_names(atom_df)

        spheres = pd.DataFrame()
        for value in shortened['atom'].unique():

            if value in var.radii:
                radius_mod = .9 * var.radii[value]
            else:
                radius_mod = .9
            print(value, ": ", radius_mod)
            coord = pdbm.rasterized_sphere(round(config_data['scale']*radius_mod))
            center = pdbm.sphere_center(round(config_data['scale']*radius_mod))
            spheres_temp = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
            spheres = pd.concat([spheres_temp, spheres], ignore_index=True)

        surface_array = pdbm.construct_surface_array(spheres)

        blurred = pdbm.blur_3d_array(surface_array, .25)
        # Save your 3D NumPy array as a 3D TIFF image
        output_path = r'C:\Users\marku\Desktop\pdb_blurred_array.tif'  # Path where you want to save the TIFF image
        pdbm.save_3d_tiff(blurred, output_path)

        blurred_bool = pdbm.contour_outline(blurred)
        # Save your 3D NumPy array as a 3D TIFF image
        output_path = r'C:\Users\marku\Desktop\pdb_blurred_bool.tif'  # Path where you want to save the TIFF image
        pdbm.save_3d_tiff(blurred_bool, output_path)

        bool_array = pdbm.contour_outline(surface_array)

        # Save your 3D NumPy array as a 3D TIFF image
        output_path = r'C:\Users\marku\Desktop\pdb_output_array.tif'  # Path where you want to save the TIFF image
        pdbm.save_3d_tiff(bool_array, output_path)

        surface_filtered_array = pdbm.filter_3d_array_with_bool(surface_array, bool_array)

        printable = surface_filtered_array.copy()
        output_path = r'C:\Users\marku\Desktop\pdb_output_filtered_array.tif'  # Path where you want to save the TIFF image
        pdbm.save_3d_tiff(printable, output_path)

        spheres = pdbm.filter_dataframe_by_array(df=spheres, arr_3d=surface_filtered_array)

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

                #Easiest way to ensure bonds are grey concrete
                hetatm_bonds['atom'] = 99
                mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
