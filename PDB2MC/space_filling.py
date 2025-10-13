from PDB2MC import minecraft_functions as mcf
import pandas as pd
import numpy as np
from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import variables as var
from itertools import cycle

def run_mode(config_data, pdb_name, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):
    print("Running space filling mode")
    cycle_sequence = cycle(range(1, 11))
    space_filling_master_df = rounded
    space_filling_total_df = pd.DataFrame()
    point_df = pd.DataFrame()
    atoms_only_df = pd.DataFrame()
    nbt_exports = []

    for chain, num in zip(enumerate(pdbm.enumerate_chains(space_filling_master_df)), cycle_sequence):
        space_filling_df = pdbm.get_chain(space_filling_master_df, chain[1])

        if config_data["by_chain"]:
            atoms_subset_df = space_filling_df[['X', 'Y', 'Z']]
            atoms_subset_df['atom'] = num
        else:
            atoms_subset_df = space_filling_df[['X', 'Y', 'Z', 'atom']]
            atoms_subset_df['atom'] = atoms_subset_df['atom'].str[0]

        branches = pdbm.sidechain(space_filling_df)
        branches['atom'] = num
        backbone = pdbm.atom_subset(space_filling_df, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"], include=True)
        intermediate = pdbm.find_intermediate_points(backbone)
        intermediate['atom'] = num
        point_list = [branches, intermediate, point_df]
        point_df = pd.concat(point_list, ignore_index=True)
        atom_list = [atoms_only_df, atoms_subset_df]
        atoms_only_df = pd.concat(atom_list, ignore_index=True)

    shortened = pdbm.shorten_atom_names(space_filling_master_df)
    coord = pdbm.rasterized_sphere(round(config_data['scale'] * .9))
    center = pdbm.sphere_center(round(config_data['scale'] * .9))
    spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
    spheres = spheres.drop_duplicates(subset=['X', 'Y', 'Z'], keep='first')
    spheres['atom'] = 'atom'
    all_points = pd.concat([spheres, point_df], ignore_index=True)
    try:
        point_np = pdbm.construct_surface_array_by_type(all_points, include=['atom', 'backbone', 'branches'])
    except Exception as e:
        print("Exception in construct_surface_array_by_type:", e)
        point_np = None

    if point_np is not None:
        bool_array = pdbm.SASA_gaussian_surface(point_np, sigma=config_data['scale'] / 1.5, fill=True)
        bool_array = np.where(bool_array >= 1, 255, 0).astype(np.uint8)
        master_bool = pdbm.find_border_cells(bool_array).astype(np.uint8)
        master_array = pdbm.array_to_voxel(master_bool, padding_size=0)
        master_array['atom'] = 0
    else:
        master_array = pd.DataFrame()

    if hetatom_df is not None:
        corner_points = pdbm.get_corner_points(point_df)
        hetatom_df = pdbm.add_corner_points(hetatom_df, corner_points)
        hetatm_bonds = pdbm.add_corner_points(hetatm_bonds, corner_points)
        aligned_dfs = pdbm.align_dataframes(point_df, master_array, atoms_only_df, hetatom_df, hetatm_bonds)
        point_df = aligned_dfs[0]
        master_array = aligned_dfs[1]
        atoms_subset_df = aligned_dfs[2]
        aligned_hetatm = aligned_dfs[3]
        aligned_hetatm_bonds = aligned_dfs[4]
        aligned_hetatm = aligned_hetatm[aligned_hetatm['atom'] != "temp"]
        aligned_hetatm_bonds = aligned_hetatm_bonds[aligned_hetatm_bonds['atom'] != "temp"]
        atoms_subset_df = atoms_subset_df[atoms_subset_df['atom'] != "H"]
    else:
        aligned_dfs = pdbm.align_dataframes(point_df, master_array, atoms_only_df)
        point_df = aligned_dfs[0]
        master_array = aligned_dfs[1]
        atoms_subset_df = aligned_dfs[2]
        aligned_hetatm = None
        aligned_hetatm_bonds = None

    if config_data['mesh']:
        master_array = pdbm.remove_random_rows(master_array, percent=90)

    output_df = pdbm.assign_atom_values(master_array, atoms_subset_df)
    pdb_surface = pdb_name + "_surface"
    pdb_branch = pdb_name + "_branch"
    point_df['atom'] = point_df['atom'].astype(str) + 'b'
    output_df['X'] = output_df['X'].astype(int).round()
    output_df['Y'] = output_df['Y'].astype(int).round()
    output_df['Z'] = output_df['Z'].astype(int).round()

    # Collect DataFrames and names for NBT export
    if not point_df.empty:
        nbt_exports.append((point_df, pdb_branch))
    if not output_df.empty:
        nbt_exports.append((output_df, pdb_surface))

    if config_data["show_hetatm"] and hetatom_df is not None and aligned_hetatm is not None:
        pdb_hetatm = pdb_name + "_hetatm"
        scale = round(config_data['scale'] - 1)
        coord = pdbm.rasterized_sphere(scale)
        center = pdbm.sphere_center(scale)
        shortened = pdbm.shorten_atom_names(aligned_hetatm)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
        if not spheres.empty:
            nbt_exports.append((spheres, pdb_hetatm))
        pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
        if aligned_hetatm_bonds is not None:
            aligned_hetatm_bonds['atom'] = 99
            if not aligned_hetatm_bonds.empty:
                nbt_exports.append((aligned_hetatm_bonds, pdb_hetatm_bonds))

    # Find the global minimum Y across all DataFrames
    all_min_ys = [df['Y'].min() for df, _ in nbt_exports if 'Y' in df.columns and not df.empty]
    if all_min_ys:
        global_min_y = min(all_min_ys)
        # Subtract the global min from all Y values in all DataFrames
        for i, (df, name) in enumerate(nbt_exports):
            if 'Y' in df.columns and not df.empty:
                nbt_exports[i] = (df.assign(Y=df['Y'] - global_min_y), name)

    # Write all NBT files at the end
    for df, name in nbt_exports:
        if df is not None and not df.empty:
            mcf.create_nbt(df, name, air=False, dir=mc_dir, blocks=config_data['atoms'])