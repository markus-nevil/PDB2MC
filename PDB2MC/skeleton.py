from PDB2MC import pdb_manipulation as pdbm
from PDB2MC import minecraft_functions as mcf
import pandas as pd
from itertools import cycle
import re
import gc

def run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):
    # Deal with the backbone
    if config_data["backbone"]:
        pdb_backbone = pdb_name + "_backbone"
        backbone = pdbm.atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                    ignore_het=True, include=True)
        if config_data["by_chain"]:
            by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
            chain_values = backbone["chain"].unique()

            for i, chain_value in enumerate(chain_values):
                # extract all rows that match the same value in "chain"
                chain_df = backbone[backbone["chain"] == chain_value]
                #print(chain_df.tail(n=25))

                # perform intermediate calculations
                intermediate = pdbm.find_intermediate_points(chain_df)
                intermediate = pdbm.cylinderize(intermediate, config_data["backbone_size"])

                # add a new column "atom" with values ranging from 1 to 10, repeating that pattern for unique "chain" values >10
                if i < 10:
                    intermediate["atom"] = i + 1
                else:
                    intermediate["atom"] = (i + 1) % 10

                # append the resulting intermediate DataFrame to by_chain_df
                by_chain_df = pd.concat([by_chain_df, intermediate], ignore_index=True)

            intermediate = by_chain_df
            del by_chain_df
        else:
            intermediate = pdbm.find_intermediate_points(backbone)
            intermediate = pdbm.cylinderize(intermediate, config_data["backbone_size"])
            #intermediate = pdbm.interpolate_dataframe(intermediate, 5000)
        #mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'], replace=False)
        mcf.create_nbt(intermediate, pdb_backbone, air=False, dir=mc_dir, blocks=config_data['atoms'])
        del intermediate
        del backbone
        gc.collect()

    if config_data["sidechain"]:
        by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
        sidechain = pdbm.atom_subset(rounded, ['N', 'P', "O5'", "C5'", "O3'"],
                                    ignore_het=True, include=False)
        chain_values = sidechain["chain"].unique()

        pdb_sidechain = pdb_name + "_sidechain"

        for i, chain_value in enumerate(chain_values):
            # extract all rows that match the same value in "chain"
            chain_df = sidechain[sidechain["chain"] == chain_value]
            branches = pdbm.sidechain(chain_df)
            if config_data["by_chain"]:
                # add a new column "atom" with values ranging from 1 to 10, repeating that pattern for unique "chain" values >10
                if i < 10:
                    branches["atom"] = i + 1
                else:
                    branches["atom"] = (i + 1) % 10
            else:
                branches['atom'] = 'sidechain_atom'

            # append the resulting intermediate DataFrame to by_chain_df
            by_chain_df = pd.concat([by_chain_df, branches], ignore_index=True)

        branches = by_chain_df

        mcf.create_nbt(branches, pdb_sidechain, air=False, dir=mc_dir, blocks=config_data['atoms'])

    if config_data["show_hetatm"]:
        if hetatom_df is not None:
            pdb_hetatm = pdb_name + "_hetatm"
            coord = pdbm.rasterized_sphere(config_data['atom_scale'])
            center = pdbm.sphere_center(config_data['atom_scale'])
            shortened = pdbm.shorten_atom_names(hetatom_df)
            spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=False)
            spheres['atom'] = spheres['atom'].apply(lambda x: re.sub(r'P[A-Z]', 'P', x, count=1))

            mcf.create_nbt(spheres, pdb_hetatm, air=False, dir=mc_dir, blocks=config_data['atoms'])
            pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
            #mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
            mcf.create_nbt(hetatm_bonds, pdb_hetatm_bonds, air=False, dir=mc_dir, blocks=config_data['atoms'])