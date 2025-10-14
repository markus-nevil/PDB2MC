from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
import pandas as pd
import re
from itertools import cycle

def run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):
    # Deal with the backbone
    print("running custom!")
    if config_data["backbone"]:
        pdb_backbone = pdb_name + "_backbone"
        backbone = pdbm.atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                    include=True)
        if config_data["by_chain"]:
            by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
            chain_values = backbone["chain"].unique()

            for i, chain_value in enumerate(chain_values):
                # extract all rows that match the same value in "chain"
                chain_df = backbone[backbone["chain"] == chain_value]

                # perform intermediate calculations
                intermediate = pdbm.find_intermediate_points(chain_df)

                # add a new column "atom" with values ranging from 1 to 10, repeating that pattern for unique "chain" values >10
                if i < 10:
                    intermediate["atom"] = i + 1
                else:
                    intermediate["atom"] = (i + 1) % 10

                # append the resulting intermediate DataFrame to by_chain_df
                by_chain_df = pd.concat([by_chain_df, intermediate], ignore_index=True)

            intermediate = by_chain_df
        else:
            intermediate = pdbm.find_intermediate_points(backbone)

            mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])
    if config_data["sidechain"]:
        if config_data["by_chain"]:
            # Create a cycle from 1 to 10 to aid in chain coloring
            cycle_sequence = cycle(range(1, 11))

            # Iterate through each chain and count the number of loops
            for chain, num in zip(enumerate(pdbm.enumerate_chains(rounded)), cycle_sequence):
                pdb_sidechain = pdb_name + "_" + chain[1] + "_sidechain"
                chain_df = pdbm.get_chain(rounded, chain[1])
                branches = pdbm.sidechain(chain_df)
                branches['atom'] = num
                mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])
        else:
            pdb_sidechain = pdb_name + "_sidechain"
            branches = pdbm.sidechain(rounded)
            branches['atom'] = 'sidechain_atom'
            mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])

    if config_data["show_atoms"]:
        pdb_atoms = pdb_name + "_atoms"
        if config_data['mesh'] and config_data['atom_scale'] < 2:
            coord = pdbm.rasterized_sphere(2)
            center = pdbm.sphere_center(2)
        else:
            coord = pdbm.rasterized_sphere(config_data['atom_scale'])
            center = pdbm.sphere_center(config_data['atom_scale'])
        shortened = pdbm.shorten_atom_names(atom_df)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
        print("I created a file!", mc_dir)
        mcf.create_nbt(spheres, pdb_atoms, air=False, dir=mc_dir, blocks=config_data['atoms'])

    if config_data["show_hetatm"]:
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
        #mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
        mcf.create_nbt(hetatm_bonds, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])