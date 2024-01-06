import pdb_manipulation as pdbm
import minecraft_functions as mcf
from itertools import cycle
import pandas as pd


def run_mode(pdb_name, pdb_file, rounded, mc_dir, config_data, hetatom_df, hetatm_bonds):
    ribbon_master_df = pdbm.add_structure(rounded, pdb_file)
    vectors_master_df = pdbm.CO_vectors(ribbon_master_df, width=0.75)
    dna_vectors_master_df = pdbm.DNA_vectors(rounded, width=0.75)

    # Create a cycle from 1 to 10 to aid in chain coloring
    cycle_sequence = cycle(range(1, 11))

    ribose_list = ["C1'", "C2'", "C3'", "C4'", "O4'"]
    base_list = ["N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9"]

    # Iterate through each chain and count the number of loops
    for chain, num in zip(enumerate(pdbm.enumerate_chains(ribbon_master_df)), cycle_sequence):
        pdb_ribbon = pdb_name + "_" + chain[1] + "_ribbon"
        ribbon_df = pdbm.get_chain(ribbon_master_df, chain[1])

        # Check that the dataframe contains amino acids
        if ribbon_df["residue"].isin(["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
                                      "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP",
                                      "TYR", "VAL"]).any():

            vectors_df = pdbm.get_chain(vectors_master_df, chain[1])
            ribbon_intermediate_df = pdbm.find_intermediate_points(ribbon_df, keep_columns=True, atoms=["CA", "C", "N"])
            ribbon_interpolated_df = pdbm.interpolate_dataframe(ribbon_intermediate_df, smoothness=5000)
            flanked_df = pdbm.flank_coordinates(ribbon_interpolated_df, vectors_df)
        # check if the dataframe contains nucleic acids
        elif ribbon_df["residue"].isin(["A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"]).any():
            flanked_df = pd.DataFrame()

            # Filter the dataframe to only include atoms in the ribose_list and base_list
            branch_ribbon_df = ribbon_df[ribbon_df["atom"].isin(ribose_list + base_list)]
            flanked_df = pdbm.sidechain(branch_ribbon_df)

        #print(flanked_df.tail())
        #print(flanked_df.head())
        if config_data["by_chain"] == False:
            flanked_df['atom'] = "ribbon_atom"
        else:
            flanked_df['atom'] = num
        print(flanked_df.head())
        mcf.create_minecraft_functions(flanked_df, pdb_ribbon, False, mc_dir, config_data['atoms'], replace=True)

        # Deal with the backbone
        pdb_backbone = pdb_name + "_" + chain[1] + "_backbone"

        # TODO: Decide how many backbone items to keep
        #backbone = pdbm.atom_subset(ribbon_df, ['C', 'N', 'CA', "O5'", "C5'", "C4'", "C3'", "O3'"], include=True)
        backbone = pdbm.atom_subset(ribbon_df, ['C', 'N', 'CA', "C4'", "C3'"], include=True)
        #Remove rows that start with 'HETATM' or have a different chain in 'chain' column from the first row
        backbone = backbone[~backbone['row'].str.startswith('HETATM')]
        backbone = backbone[~backbone['chain'].isin(backbone['chain'].unique()[1:])]
        if ribbon_df["residue"].isin(["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS",
                                      "ILE", "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP",
                                      "TYR", "VAL"]).any():
            print(backbone.tail())
            intermediate = pdbm.find_intermediate_points(backbone)
            intermediate = pdbm.interpolate_dataframe(intermediate, 5000)

        elif ribbon_df["residue"].isin(["A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"]).any():
            intermediate = pdbm.find_intermediate_points(backbone, keep_columns=True)
            intermediate = pdbm.interpolate_dataframe(intermediate, 5000)
            intermediate = pdbm.flank_DNA(intermediate, dna_vectors_master_df)
            #Filter to ensure intermediate is only X, Y, Z columns
            intermediate = intermediate.filter(['X', 'Y', 'Z'])

        #Convert all values in intermediate to int from float64
        intermediate = intermediate.astype(int)

        #Add a column to intermediate called 'atom' with values of num, if 'atom' exists, then add the values of num to the column
        if config_data["by_chain"] == False:
            intermediate['atom'] = "backbone_atom"
        else:
            intermediate['atom'] = num

        mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'], replace=False)

    if config_data["show_hetatm"] == True:
        if hetatom_df is not None:
            pdb_hetatm = pdb_name + "_hetatm"
            coord = pdbm.rasterized_sphere(1.5)
            center = pdbm.sphere_center(1.5)
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened)

            ##TODO Make this user configurable
            mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'], replace=True)

            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
