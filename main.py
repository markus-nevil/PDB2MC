from pdb_manipulation import *
from plotting_functions import *
from minecraft_functions import *
import PySimpleGUI as sg
from variables import *
import pandas as pd
import ast
import json
import shutil

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
                "ALA": "stone",
                "ARG": "cobblestone",
                "ASN": "dirt",
                "ASP": "oak_planks",
                "CYS": "spruce_planks",
                "GLN": "birch_planks",
                "GLU": "jungle_planks",
                "GLY": "acacia_planks",
                "HIS": "dark_oak_planks",
                "ILE": "sandstone",
                "LEU": "terracotta",
                "LYS": "nether_brick",
                "MET": "prismarine_bricks",
                "PHE": "polished_granite",
                "PRO": "end_stone_bricks",
                "SER": "red_nether_bricks",
                "THR": "redstone_block",
                "TRP": "obsidian",
                "TYR": "polished_andesite",
                "VAL": "polished_diorite",
                "A": "pink_wool",
                "U": "lime_wool",
                "G": "gray_wool",
                "C": "light_blue_wool",
                "dA": "red_wool",
                "dT": "green_wool",
                "dG": "black_wool",
                "dC": "blue_wool"
            },
            "mode": "Default",
            "backbone": True,
            "backbone_size": 1,
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
    window = sg.Window("Select plotting mode", open_layout)

    #Create the popup window and hide it
    preset_window = sg.Window("Preset Models", preset_layout, finalize=True)
    preset_window.hide()

    # Loop to keep the window open
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break
        elif event == 'Switch Layout':
            if window['mode'].get() == 'Custom':
                master_mode = "Custom"
                window.close()
                window = sg.Window("Default Plotting options", default_layout)
            elif window['mode'].get() == 'Backbone' or window['mode'].get() == 'Skeleton':
                master_mode = "Skeleton"
                window.close()
                window = sg.Window("Backbone/Skeleton Plotting Options", backbone_layout)
            elif window['mode'].get() == 'Space Filling':
                master_mode = "Space Filling"
                window.close()
                window = sg.Window("Space Filling Plotting Options", sf_layout)
            elif window['mode'].get() == 'X-ray' or window['mode'].get() == 'X-ray Backbone':
                master_mode = "X-ray Backbone"
                window.close()
                window = sg.Window("X-ray Plotting Options", xray_layout)
            elif window['mode'].get() == 'Amino Acids':
                master_mode = "Amino Acids"
                window.close()
                window = sg.Window("Amino Acid Plotting Options", aa_layout)
            elif window['mode'].get() == 'Ribbon':
                master_mode = "Ribbon"
                window.close()
                window = sg.Window("Ribbon Plotting Options", ribbon_layout)

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

            # check if pdb_file contains a string
            if type(preset_file) == str:
                # check if the model is small enough for minecraft
                if not check_model_size(preset_file, world_max=320):
                    sg.popup("Model may be too large for Minecraft.")
                else:
                    # Calculate the maximum protein scale factor
                    size_factor = check_max_size(preset_file, world_max=320)
                    size_factor = str(round(size_factor, 2))
                    sg.popup("The maximum protein scale is: " + size_factor + "x")

        if event == "Select PDB file":
            pdb_file = sg.popup_get_file("Select PDB file")
            # Save the pdb_file path to config.json
            with open("config.json", "r+") as f:
                config = json.load(f)
                config["pdb_file"] = pdb_file
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
            # check if pdb_file contains a string
            if type(pdb_file) == str:
                # check if the model is small enough for minecraft
                if not check_model_size(pdb_file, world_max=320):
                    sg.popup("Model may be too large for Minecraft.")
                else:
                    # Calculate the maximum protein scale factor
                    size_factor = check_max_size(pdb_file, world_max=320)
                    size_factor = str(round(size_factor, 2))
                    sg.popup("The maximum protein scale is: " + size_factor + "x")
        if event == "Select Minecraft Save":
            home_dir = os.path.expanduser("~")
            appdata_dir = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")
            good_dir = False

            while not good_dir:
                save_path = sg.popup_get_folder("Select your Minecraft save file", initial_folder=appdata_dir)

                # check if save_path has structure .minecraft/saves/<save_name>
                if save_path:
                    if os.path.basename(os.path.dirname(save_path)) == "saves":
                        good_dir = True
                    else:
                        sg.popup("You didn't select a Minecraft save file! Try again!")

            directory_path = os.path.join(save_path, "datapacks/mcPDB/data/protein/functions")
            #print(directory_path, " is where you are going to save your functions")
            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            # check for pack.mcmeta in the /datapacks/mcPDB folder and if not copy it from the python directory
            if not os.path.isfile(os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta")):
                shutil.copyfile("pack.mcmeta", os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

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
                    if values.get('C') is not None:
                        config["atoms"]["C"] = values["C"]
                        config["atoms"]["N"] = values["N"]
                        config["atoms"]["O"] = values["O"]
                        config["atoms"]["S"] = values["S"]
                        config["atoms"]["P"] = values["P"]
                        # config["atoms"]["H"] = values["H"]
                    config["atoms"]["backbone_atom"] = values.get("backbone_atom")
                    config["atoms"]["sidechain_atom"] = values.get("sidechain_atom")
                    config["atoms"]["other_atom"] = values.get("other_atom")
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
                    config["mode"] = values.get("mode")
                    config["backbone"] = values.get("backbone")
                    config["backbone_size"] = values.get("backbone_size")
                    config["sidechain"] = values.get("sidechain")
                    config["by_chain"] = values.get("by_chain")
                    config["show_atoms"] = values.get("show_atoms")
                    config["show_hetatm"] = values.get("show_hetatm")
                    config["mesh"] = values.get("mesh")
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
                pdb_name = get_pdb_code(pdb_file)
                scalar = config_data['scale']
                scaled = scale_coordinates(pdb_df, scalar)
                moved = move_coordinates(scaled)
                moved = rotate_to_y(moved)
                rounded = round_df(moved)

                mc_dir = config_data['save_path']
                #print(mc_dir)
                delete_mcfunctions(mc_dir, pdb_name.lower())

                # Check if the user wants het-atoms, if so, process them
                if config_data["show_hetatm"] == True:
                    hetatm_bonds = process_hetatom(rounded, pdb_file)
                    hetatom_df = filter_type_atom(rounded, remove_type="ATOM", remove_atom="H")

                atom_df = filter_type_atom(rounded, remove_type="HETATM", remove_atom="H")


                print(config_data["mode"])
                # Check if printing a special case
                if master_mode == "Amino Acids":
                    print("Amino acid mode")
                    residue = atom_subset(rounded, ['CA', "C4'"], include=True)

                    pdb_atoms = pdb_name + "_atoms"
                    coord = rasterized_sphere(config_data['atom_scale'])
                    center = sphere_center(config_data['atom_scale'])
                    shortened = residue_to_atoms(residue)

                    # Hard coded the "mesh" due to lack in the config file
                    spheres = fill_sphere_coordinates(coord, center, shortened)

                    create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['amino_acids'],
                                                   replace=True)

                    if config_data["backbone"] == True:
                        pdb_backbone = pdb_name + "_backbone"
                        backbone = atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                               include=True)

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

                        cyl_diameter = float(config_data['backbone_size'])
                        intermediate = cylinderize(intermediate, cyl_diameter)
                        intermediate = remove_inside_spheres(spheres, intermediate, 2)
                        create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                                       replace=False)



                # Otherwise print a normal model
                else:


                    if master_mode == "Ribbon":
                        pdb_ribbon = pdb_name + "_ribbon"
                        ribbon_df = add_structure(rounded, pdb_file)
                        vectors_df = CO_vectors(ribbon_df, width=0.75)
                        print("Ribbon with structure: ", ribbon_df.tail(n=5))

                        #ribbon_df = smooth_line(ribbon_df)
                        ribbon_df = find_intermediate_points(ribbon_df, keep_columns=True, atoms=["CA", "C", "N"])
                        ribbon_df = interpolate_dataframe(ribbon_df, smoothness=5000)
                        print("Smoothed: ", ribbon_df.tail(n=5))

                        flanked_df = flank_coordinates(ribbon_df, vectors_df)
                        print("Flanked: ", flanked_df.tail(n=5))

                        #replace the 'atom' column values to 'O' for the ribbon
                        flanked_df['atom'] = 'O'

                        #flanked_df = add_missing_coordinates(flanked_df)

                        create_minecraft_functions(flanked_df, pdb_ribbon, False, mc_dir, config_data['atoms'], replace=True)

                    if config_data["backbone"] == True or master_mode == "Ribbon":
                        pdb_backbone = pdb_name + "_backbone"
                        backbone = atom_subset(rounded, ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"],
                                               include=True)

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
                            intermediate = interpolate_dataframe(intermediate, 5000)

                        if config_data["mode"] == "X-ray":
                            create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                                       replace=True)
                        else:
                            create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'],
                                                       replace=False)

                    if config_data["sidechain"] == True and master_mode != "Amino Acids":

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
