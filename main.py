from pdb_manipulation import *
from plotting_functions import *
from minecraft_functions import *
import PySimpleGUI as sg
from variables import *
import pandas as pd
import ast
import json

if __name__ == '__main__':

    # Check if the config file exists
    if not os.path.isfile("config.json"):
        # If it doesn't exist, create it
        config = {
            "scale": 1.0,
            "atoms": {
                "C": "black_concrete",
                "O": "red_concrete",
                "N": "blue_concrete",
                "S": "yellow_concrete",
                "P": "lime_concrete",
                "FE": "iron_block",
                "backbone_atom": "gray_concrete",
                "sidechain_atom": "gray_concrete",
                "other_atom": "pink_concrete"
            },
            "amino_acids": {
                "ALA": "red_concrete",
                "ARG": "",
                "ASN": "",
                "ASP": "",
                "CYS": "",
                "GLN": "",
                "GLU": "",
                "GLY": "",
                "HIS": "",
                "ILE": "",
                "LEU": "",
                "LYS": "",
                "MET": "",
                "PHE": "",
                "PRO": "",
                "SER": "",
                "THR": "",
                "TRP": "",
                "TYR": "",
                "VAL": ""
            },
            "mode": "Default",
            "backbone": True,
            "sidechain": True,
            "show_atoms": True,
            "by_chain": False,
            "show_hetatm": True,
            "mesh": False,
            "pdb_file": None,
            "save_path": None
        }
        with open("config.json", "w") as f:
            json.dump(config, f)

    # Otherwise load in the existing config and make sure the paths are reset to None
    else:
        with open("config.json", "r+") as f:
            config = json.load(f)
            config["save_path"] = None
            config["pdb_file"] = None
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()

    # Create the window
    window = sg.Window("My Window", open_layout)

    #Create the popup window and hide it
    preset_window = sg.Window("Preset Models", preset_layout, finalize=True)
    preset_window.hide()

    # Loop to keep the window open
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
        elif event == 'Switch Layout':
            if window['mode'].get() == 'Default':
                window.close()
                window = sg.Window("Default Plotting options", default_layout)
            elif window['mode'].get() == 'Backbone' or window['mode'].get() == 'Skeleton':
                window.close()
                window = sg.Window("Backbone/Skeleton Plotting Options", backbone_layout)
            elif window['mode'].get() == 'Space Filling':
                window.close()
                window = sg.Window("Space Filling Plotting Options", sf_layout)
            elif window['mode'].get() == 'X-ray' or window['mode'].get() == 'X-ray Backbone':
                window.close()
                window = sg.Window("X-ray Plotting Options", xray_layout)
            elif window['mode'].get() == 'Amino Acids':
                window.close()
                window = sg.Window("Amino Acid Plotting Options", aa_layout)
            elif window['mode'].get() == 'Min' or window['mode'].get() == 'Max':
                window.close()
                window = sg.Window("Min/Max Plotting Options", minmax_layout)

        if event == 'Select Included PDB file':
            cwd = os.getcwd()
            filepath = os.path.join(cwd, "presets")
            preset_file = sg.popup_get_file("Select Included PDB File", initial_folder=filepath)
            with open("config.json", "r+") as f:
                config = json.load(f)
                config["pdb_file"] = preset_file
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

        if event == "Select PDB file":
            pdb_file = sg.popup_get_file("Select PDB file")
            # Save the pdb_file path to config.json
            with open("config.json", "r+") as f:
                config = json.load(f)
                config["pdb_file"] = pdb_file
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

        if event == "Select Minecraft Save":
            home_dir = os.path.expanduser("~")
            appdata_dir = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")

            save_path = sg.popup_get_folder("Select Minecraft 'datapacks' in your save", initial_folder=appdata_dir)

            directory_path = os.path.join(save_path, "mcPDB/data/protein/functions")
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            # Save the save_path to config.json
            with open("config.json", "r+") as f:
                config = json.load(f)
                config["save_path"] = directory_path
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

        if event == "Create Minecraft Functions":

            # Execute further code here
            if config["save_path"] and config["pdb_file"]:
                # Save the window variables to config.json
                with open("config.json", "r+") as f:

                    config = json.load(f)
                    config["scale"] = float(values["scale"])
                    config["atom_scale"] = float(values["atom_scale"])
                    config["atoms"]["C"] = values["C"]
                    config["atoms"]["N"] = values["N"]
                    config["atoms"]["O"] = values["O"]
                    config["atoms"]["S"] = values["S"]
                    config["atoms"]["P"] = values["P"]
                    # config["atoms"]["H"] = values["H"]
                    config["atoms"]["backbone_atom"] = values["backbone_atom"]
                    config["atoms"]["sidechain_atom"] = values["sidechain_atom"]
                    config["atoms"]["other_atom"] = values["other_atom"]
                    if values.get('ALA') is not None:
                        config["amino_acids"]["ALA"] = values["ALA"]
                        config["amino_acids"]["ARG"] = values["ARG"]
                        config["amino_acids"]["ASN"] = values["ASN"]
                        config["amino_acids"]["ASP"] = values["ASP"]
                        config["amino_acids"]["CYS"] = values["CYS"]
                        config["amino_acids"]["GLN"] = values["GLN"]
                        config["amino_acids"]["GLU"] = values["GLU"]
                        config["amino_acids"]["GLY"] = values["GLY"]
                        config["amino_acids"]["HIS"] = values["HIS"]
                        config["amino_acids"]["ILE"] = values["ILE"]
                        config["amino_acids"]["LEU"] = values["LEU"]
                        config["amino_acids"]["LYS"] = values["LYS"]
                        config["amino_acids"]["MET"] = values["MET"]
                        config["amino_acids"]["PHE"] = values["PHE"]
                        config["amino_acids"]["PRO"] = values["PRO"]
                        config["amino_acids"]["SER"] = values["SER"]
                        config["amino_acids"]["THR"] = values["THR"]
                        config["amino_acids"]["TRP"] = values["TRP"]
                        config["amino_acids"]["TYR"] = values["TYR"]
                        config["amino_acids"]["VAL"] = values["VAL"]
                    config["mode"] = values["mode"]
                    config["backbone"] = values["backbone"]
                    config["sidechain"] = values["sidechain"]
                    config["by_chain"] = values["by_chain"]
                    config["show_atoms"] = values["show_atoms"]
                    config["show_hetatm"] = values["show_hetatm"]
                    config["mesh"] = values["mesh"]
                    f.seek(0)
                    json.dump(config, f, indent=4, default=None)
                    f.truncate()

                f = open('config.json')
                config_data = json.load(f)
                f.close

                if config_data["mode"] != "Default":
                    config_data = change_mode(config_data)

                pdb_file = config_data['pdb_file']

                pdb_df = read_pdb(pdb_file)
                # print(pdb_df.head(n=20))
                # print(pdb_df.tail(n=20))

                pdb_name = get_pdb_code(pdb_file)

                scalar = config_data['scale']
                # clipped = clip_coords(pdb_df)
                # print(pdb_df.head(n=40))
                # print(clipped.head(n=40))
                # scaled = scale_coordinates(clipped, scalar)
                # print(pdb_df.head(n=5))
                scaled = scale_coordinates(pdb_df, scalar)
                # print(scaled.head(n=5))
                moved = move_coordinates(scaled)
                # print(moved.head(n=5))
                rounded = round_df(moved)
                #print(rounded.tail(n=100))

                mc_dir = config_data['save_path']

                hetatm_bonds = process_hetatom(rounded, pdb_file)

                hetatom_df = filter_type_atom(rounded, remove_type="ATOM", remove_atom="H")
                atom_df = filter_type_atom(rounded, remove_type="HETATM", remove_atom="H")

                # Check if printing a special case
                if config_data["mode"] == "Amino Acids":
                    print("Amino acid mode")

                # Otherwise print a normal model
                else:
                    delete_mcfunctions(mc_dir, pdb_name.lower())

                    if config_data["backbone"] == True:
                        pdb_backbone = pdb_name + "_backbone"
                        backbone = atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                               include=True)
                        #print(backbone)
                        if config_data["by_chain"]:
                            by_chain_df = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])
                            chain_values = backbone["chain"].unique()

                            for i, chain_value in enumerate(chain_values):
                                # extract all rows that match the same value in "chain"
                                chain_df = backbone[backbone["chain"] == chain_value]

                                # perform intermediate calculations
                                intermediate = find_intermediate_points(chain_df)

                                # add a new column "atom" with values ranging from 1 to 10, repeating that pattern for unique "chain" values >10
                                if i < 10:
                                    intermediate["atom"] = i+1
                                else:
                                    intermediate["atom"] = (i+1) % 10

                                # append the resulting intermediate DataFrame to by_chain_df
                                by_chain_df = pd.concat([by_chain_df, intermediate], ignore_index=True)

                            intermediate = by_chain_df
                        else:
                            intermediate = find_intermediate_points(backbone)
                        if config_data["mode"] == "X-ray":
                            create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                                       replace=True)
                        else:
                            create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                                       replace=False)

                    if config_data["sidechain"] == True:
                        branches = sidechain(rounded)

                        if config_data["by_chain"]:
                            branches = branches.drop("atom", axis=1)

                        pdb_sidechain = pdb_name + "_sidechain"

                        if config_data["mode"] == "X-ray":
                            create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'],
                                                       replace=True)
                        else:
                            create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'],
                                                       replace=False)

                    if config_data["show_atoms"] == True:
                        pdb_atoms = pdb_name + "_atoms"
                        coord = rasterized_sphere(config_data['atom_scale'])
                        center = sphere_center(config_data['atom_scale'])
                        shortened = shorten_atom_names(atom_df)
                        spheres = add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                        #print(spheres)
                        if config_data["mode"] == "X-ray":
                            create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'],
                                                       replace=False)
                        else:
                            create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'],
                                                       replace=True)
                    if config_data["show_hetatm"] == True:
                        pdb_hetatm = pdb_name + "_hetatm"
                        coord = rasterized_sphere(config_data['atom_scale'])
                        center = sphere_center(config_data['atom_scale'])
                        shortened = shorten_atom_names(hetatom_df)
                        spheres = add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                        if config_data["mode"] == "X-ray":
                            create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'],
                                                       replace=False)
                        else:
                            create_minecraft_functions(spheres, pdb_hetatm, False, mc_dir, config_data['atoms'],
                                                       replace=True)
                        pdb_hetatm_bonds = pdb_name + "_hetatm_bonds"
                        create_minecraft_functions(hetatm_bonds, pdb_hetatm_bonds, False, mc_dir, config_data['atoms'])

                mcfiles = find_mcfunctions(mc_dir, pdb_name.lower())
                print(mcfiles)
                print(config_data)

                create_master_function(mcfiles, pdb_name, mc_dir)

                message = f"Finished! Remember to /reload in your world and /function protein:drop_{pdb_name}"
                sg.popup(message)
            else:

                sg.Popup("You are missing a PDB file and/or a save directory!", title="Warning!")

    # Close the window
    window.close()
