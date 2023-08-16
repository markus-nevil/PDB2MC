import pdb_manipulation as pdbm
import minecraft_functions as mcf
import pandas as pd


def run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds):
    # Deal with the backbone
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
            #intermediate = pdbm.interpolate_dataframe(intermediate, 5000)

        if config_data["mode"] == "X-ray":
            mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                           replace=True)
        else:
            mcf.create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                           replace=False)

    if config_data["sidechain"]:

        branches = pdbm.sidechain(rounded)

        if not config_data["by_chain"]:
            branches = branches.drop("atom", axis=1)

        pdb_sidechain = pdb_name + "_sidechain"

        if config_data["mode"] == "X-ray":
            mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'],
                                           replace=True)
        else:
            mcf.create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'],
                                           replace=False)

    if config_data["show_atoms"]:
        pdb_atoms = pdb_name + "_atoms"
        coord = pdbm.rasterized_sphere(config_data['atom_scale'])
        center = pdbm.sphere_center(config_data['atom_scale'])
        shortened = pdbm.shorten_atom_names(atom_df)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])

        if config_data["mode"] == "X-ray":
            mcf.create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'],
                                           replace=False)
        else:
            mcf.create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'],
                                           replace=True)
    if config_data["show_hetatm"]:
        pdb_hetatm = pdb_name + "_hetatm"
        coord = pdbm.rasterized_sphere(config_data['atom_scale'])
        center = pdbm.sphere_center(config_data['atom_scale'])
        shortened = pdbm.shorten_atom_names(hetatom_df)
        spheres = pdbm.add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
        if config_data["mode"] == "X-ray":
            mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'],
                                           replace=False)
        else:
            mcf.create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'],
                                           replace=True)
        pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
        mcf.create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])
