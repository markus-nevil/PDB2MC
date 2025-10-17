from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
from PDB2MC.variables import group, charge, hydrophobic
import pandas as pd
import re

def run_mode(structure, config_data, pdb_name, mc_dir):
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

    # Subset for residues
    residue = pdbm.atom_subset(df, ['CA', "C4'"], include=True)

    pdb_atoms = pdb_name + "_atoms"
    coord = pdbm.rasterized_sphere(config_data['atom_scale'])
    coord[coord == 1] = 255
    coord = pdbm.find_border_cells(coord)
    coord[coord == 255] = 1
    center = pdbm.sphere_center(config_data['atom_scale'])
    shortened = pdbm.residue_to_atoms(residue)

    spheres = pdbm.fill_sphere_coordinates(coord, center, shortened)

    dna_bases = {"DA": "lime_concrete",
                 "DC": "blue_concrete",
                 "DG": "black_concrete",
                 "DT": "red_concrete",
                 "A": "lime_wool",
                 "C": "blue_wool",
                 "G": "black_wool",
                 "T": "red_wool"}

    if config_data["color_style"] == "group":
        combined_dictionary = {**group, **dna_bases}
    elif config_data["color_style"] == "charge":
        combined_dictionary = {**charge, **dna_bases}
    elif config_data["color_style"] == "hydrophobic":
        combined_dictionary = {**hydrophobic, **dna_bases}
    else:
        combined_dictionary = {**config_data['amino_acids'], **dna_bases}

    mcf.create_nbt(spheres, pdb_atoms, air=False, dir=mc_dir, blocks=combined_dictionary)

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
        intermediate = pdbm.remove_inside_spheres(spheres, intermediate, 2)
        mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # Sidechain
    # if config_data["sidechain"]:
    #     branches = pdbm.sidechain(df)
    #     if config_data["by_chain"]:
    #         branches = branches.drop("atom", axis=1)
    #     pdb_sidechain = pdb_name + "_sidechain"
    #     mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # Atom spheres
    if config_data.get("show_atoms", False):
        pdb_atoms = pdb_name + "_atoms"
        coord = pdbm.rasterized_sphere(config_data['atom_scale'])
        center = pdbm.sphere_center(config_data['atom_scale'])
        atom_df = pdbm.filter_type_atom(df, remove_type="HETATM", remove_atom="H")
        shortened = pdbm.shorten_atom_names(atom_df)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data.get('mesh', False))
        mcf.create_nbt(spheres, pdb_atoms, air=False, dir=mc_dir, blocks=config_data['atoms'])

    # HETATM
    if config_data["show_hetatm"]:
        hetatom_df = pdbm.filter_type_atom(df, remove_type="ATOM", remove_atom="H")
        hetatm_bonds = pdbm.get_hetatm_bond_lines_from_df(hetatom_df, getattr(structure, "bonds", None))
        if hetatom_df is not None and not hetatom_df.empty:
            pdb_hetatm = pdb_name + "_hetatm"
            coord = pdbm.rasterized_sphere(config_data['atom_scale'])
            center = pdbm.sphere_center(config_data['atom_scale'])
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data.get('mesh', False))
            spheres['atom'] = spheres['atom'].apply(lambda x: re.sub(r'P[A-Z]', 'P', x, count=1))
            mcf.create_nbt(spheres, pdb_hetatm, air=False, dir=mc_dir, blocks=config_data['atoms'])
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            if hetatm_bonds is not None and not hetatm_bonds.empty:
                mcf.create_nbt(hetatm_bonds, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])
