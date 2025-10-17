from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
from itertools import cycle
import pandas as pd
import re


def run_mode(config_data, pdb_name, structure, mc_dir, hetatom_df, hetatm_bonds):
    # Build main DataFrame from StructureData atoms
    ribbon_master_df = pd.DataFrame(structure.atoms)
    # Standardize coordinate and atom columns
    if 'x' in ribbon_master_df.columns:
        ribbon_master_df = ribbon_master_df.rename(columns={'x': 'X', 'y': 'Y', 'z': 'Z'})
    if 'hetatm' in ribbon_master_df.columns:
        ribbon_master_df['row'] = ribbon_master_df['hetatm'].apply(lambda h: 'HETATM' if h else 'ATOM')
    else:
        ribbon_master_df['row'] = 'ATOM'
    if 'atom' in ribbon_master_df.columns:
        ribbon_master_df['atom'] = ribbon_master_df['atom'].astype(str)
    # Apply coordinate transformations
    ribbon_master_df = pdbm.scale_coordinates(ribbon_master_df, config_data['scale'])
    ribbon_master_df = pdbm.move_coordinates(ribbon_master_df)
    ribbon_master_df = pdbm.rotate_to_y(ribbon_master_df)
    ribbon_master_df = pdbm.round_df(ribbon_master_df)

    # Annotate secondary structure using StructureData
    ribbon_master_df = pdbm.add_structure_from_structured_data(ribbon_master_df, structure)

    intermediate = pd.DataFrame()
    bar_helix = config_data['bar_style']

    # --- HETATM handling ---
    hetatom_df_local = None
    hetatm_bonds_local = None
    if config_data["show_hetatm"]:
        # Extract HETATM rows before removing them from main DataFrame
        hetatom_df_local = pdbm.filter_type_atom(ribbon_master_df, remove_type="ATOM", remove_atom="H")
        hetatm_bonds_local = pdbm.get_hetatm_bond_lines_from_df(hetatom_df_local, structure.bonds)

    # Remove HETATM rows for main ribbon processing
    ribbon_master_df = ribbon_master_df[~ribbon_master_df['row'].str.startswith('HETATM')]

    # Precompute vectors for backbone and DNA
    vectors_master_df = pdbm.CO_vectors(ribbon_master_df, width=1)
    dna_vectors_master_df = pdbm.DNA_vectors(ribbon_master_df, width=1)

    # Chain coloring and atom lists for nucleic acids
    cycle_sequence = cycle(range(1, 11))
    ribose_list = ["C1'", "C2'", "C3'", "C4'", "O4'"]
    base_list = ["N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9"]

    # Iterate through each chain and process ribbon/backbone
    for chain, num in zip(enumerate(pdbm.enumerate_chains(ribbon_master_df)), cycle_sequence):
        pdb_ribbon = f"{pdb_name}_{chain[1]}_ribbon"
        pdb_bonds = f"{pdb_name}_{chain[1]}_bonds"

        ribbon_df = pdbm.get_chain(ribbon_master_df, chain[1])

        # Protein chain: process ribbon and backbone
        if ribbon_df["residue"].isin([
            "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
            "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRW",
            "TYR", "VAL"
        ]).any():
            vectors_df = pdbm.get_chain(vectors_master_df, chain[1])
            ribbon_intermediate_df = pdbm.find_intermediate_points(ribbon_df, keep_columns=True, atoms=["CA", "C", "N"])
            ribbon_interpolated_df = pdbm.interpolate_dataframe(ribbon_intermediate_df, smoothness=5000)
            # Flank coordinates if helix/sheet present
            if ribbon_df['structure'].str.contains('helix').any() or ribbon_df['structure'].str.contains('sheet').any():
                try:
                    flanked_df = pdbm.flank_coordinates(ribbon_interpolated_df, vectors_df, bar=bar_helix)
                except Exception:
                    flanked_df = ribbon_interpolated_df
            else:
                flanked_df = ribbon_interpolated_df

        # Nucleic acid chain: process sidechain
        elif ribbon_df["residue"].isin([
            "A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"
        ]).any():
            branch_ribbon_df = ribbon_df[ribbon_df["atom"].isin(ribose_list + base_list)]
            flanked_df = pdbm.sidechain(branch_ribbon_df)

        # Skip chains with no recognized residues
        else:
            continue

        # Optionally add backbone bars for protein chains
        if bar_helix and ribbon_df["residue"].isin([
            "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
            "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRW",
            "TYR", "VAL"
        ]).any():
            backbone = pdbm.atom_subset(ribbon_df, ['C', 'N', 'CA', "C4'", "C3'"], include=True)
            backbone = backbone[~backbone['row'].str.startswith('HETATM')]
            backbone = backbone[~backbone['chain'].isin(backbone['chain'].unique()[1:])]
            if ribbon_df["residue"].isin([
                "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
                "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRW",
                "TYR", "VAL"
            ]).any():
                intermediate = pdbm.find_intermediate_points(backbone, fill_columns=True, keep_columns=True)
                intermediate = pdbm.interpolate_dataframe(intermediate, 5000)
                if ribbon_df['structure'].str.contains('helix').any():
                    intermediate = intermediate[~intermediate['structure'].str.contains('helix')]
                    intermediate = intermediate.reset_index(drop=True)
                    result_df = pdbm.process_bars(intermediate, size=config_data['scale'] * 2)
                # Add dummy columns to result_df
                result_df['row'] = "A"
                result_df['atom_num'] = 1
                result_df['atom'] = "C"
                result_df['residue'] = "ALA"
                result_df['chain'] = "A"
                result_df['resid'] = 1
                result_df['structure'] = "helix"
                flanked_df = pd.concat([flanked_df, result_df], ignore_index=True)

        # Set atom type for output
        flanked_df['atom'] = num if config_data["by_chain"] else "ribbon_atom"
        mcf.create_nbt(flanked_df, pdb_ribbon, air=False, dir=mc_dir, blocks=config_data['atoms'])

        # Backbone output
        pdb_backbone = f"{pdb_name}_{chain[1]}_backbone"
        backbone = pdbm.atom_subset(ribbon_df, ['C', 'N', 'CA', "C4'", "C3'"], include=True)
        backbone = backbone[~backbone['row'].str.startswith('HETATM')]
        backbone = backbone[~backbone['chain'].isin(backbone['chain'].unique()[1:])]

        if ribbon_df["residue"].isin([
            "ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
            "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRW",
            "TYR", "VAL"
        ]).any():
            intermediate = pdbm.find_intermediate_points(backbone, fill_columns=True, keep_columns=True)
            intermediate = pdbm.interpolate_dataframe(intermediate, 5000)
            if bar_helix:
                if ribbon_df['structure'].str.contains('helix').any():
                    intermediate = intermediate[~intermediate['structure'].str.contains('helix')]
                if ribbon_df['structure'].str.contains('sheet').any():
                    intermediate = intermediate[~intermediate['structure'].str.contains('sheet')]
                intermediate = intermediate.filter(['X', 'Y', 'Z'])
        elif ribbon_df["residue"].isin([
            "A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"
        ]).any():
            intermediate = pdbm.find_intermediate_points(backbone, keep_columns=True)
            intermediate = pdbm.interpolate_dataframe(intermediate, 5000)
            intermediate = pdbm.flank_DNA(intermediate, dna_vectors_master_df)
            intermediate = intermediate.filter(['X', 'Y', 'Z'])

        intermediate[['X', 'Y', 'Z']] = intermediate[['X', 'Y', 'Z']].astype(int)
        intermediate['atom'] = num if config_data["by_chain"] else "backbone_atom"
        mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # Output HETATM spheres and bonds if requested
    if config_data["show_hetatm"]:
        if hetatom_df_local is not None and not hetatom_df_local.empty:
            pdb_hetatm = f"{pdb_name}_hetatm"
            coord = pdbm.rasterized_sphere(1.5)
            center = pdbm.sphere_center(1.5)
            shortened = pdbm.shorten_atom_names(hetatom_df_local)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened)
            spheres['atom'] = spheres['atom'].apply(lambda x: re.sub(r'P[A-Z]', 'P', x, count=1))
            mcf.create_nbt(spheres, pdb_hetatm, air=False, dir=mc_dir, blocks=config_data['atoms'])

            pdb_hetatm_bonds = f"{pdb_name}_hetatm_bonds"
            if hetatm_bonds_local is not None and not hetatm_bonds_local.empty:
                mcf.create_nbt(hetatm_bonds_local, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])
