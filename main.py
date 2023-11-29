import pdb_manipulation as pdbm
import minecraft_functions as mcf
import custom as custom
import skeleton as skeleton
import space_filling as space_filling
import xray as xray
import amino_acids as amino_acids
import ribbon as ribbon
import PySimpleGUI as sg
import pandas as pd
import json
import shutil
import variables
import os

if __name__ == '__main__':

    # Check if the config file exists
    if not os.path.isfile(variables.config_path):
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
            "simple": True,
            "pdb_file": None,
            "save_path": None
        }
        # Check if the directory exists
        if not os.path.exists('docs'):
            # If it doesn't exist, create it
            os.makedirs('docs')

        #save the config file to /docs/config.json
        with open(variables.config_path, "w") as f:
            json.dump(config, f, indent=4)

    # Otherwise load in the existing config and make sure the paths are reset to None
    else:
        with open(variables.config_path, "r+") as f:
            config = json.load(f)
            config["save_path"] = None
            config["pdb_file"] = None
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()

    # Create the window
    window = sg.Window("Select plotting mode", variables.open_layout)

    #Create the popup window and hide it
    preset_window = sg.Window("Preset Models", variables.preset_layout, finalize=True)
    preset_window.hide()

    # Loop to keep the window open
    while True:
        event, values = window.read()
        master_mode = ""
        hetatom_df = pd.DataFrame()
        hetatm_bonds = pd.DataFrame()

        if event == sg.WIN_CLOSED:
            break
        elif event == 'Switch Layout':
            if window['mode'].get() == 'Custom':
                master_mode = "Custom"
                window.close()
                window = sg.Window("Default Plotting options", variables.default_layout)
            elif window['mode'].get() == 'Skeleton':
                master_mode = "Skeleton"
                window.close()
                window = sg.Window("Skeleton Plotting Options", variables.backbone_layout)
            elif window['mode'].get() == 'Space Filling':
                master_mode = "Space Filling"
                window.close()
                window = sg.Window("Space Filling Plotting Options", variables.sf_layout)
            elif window['mode'].get() == 'X-ray' or window['mode'].get() == 'X-ray Backbone':
                master_mode = "X-ray Backbone"
                window.close()
                window = sg.Window("X-ray Plotting Options", variables.xray_layout)
            elif window['mode'].get() == 'Amino Acids':
                master_mode = "Amino Acids"
                window.close()
                window = sg.Window("Amino Acid Plotting Options", variables.aa_layout)
            elif window['mode'].get() == 'Ribbon':
                master_mode = "Ribbon"
                window.close()
                window = sg.Window("Ribbon Plotting Options", variables.ribbon_layout)

        # If the user selects a preset model, open the preset window
        if event == 'Select Included PDB file':
            cwd = os.getcwd()
            filepath = os.path.join(cwd, "presets")
            preset_file = sg.popup_get_file("Select Included PDB File", initial_folder=filepath)
            with open(variables.config_path, "r+") as f:
                config = json.load(f)
                config["pdb_file"] = preset_file
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

            # check if pdb_file contains a string
            if type(preset_file) == str:
                # check if the model is small enough for minecraft
                if not pdbm.check_model_size(preset_file, world_max=320):
                    sg.popup("Model may be too large for Minecraft.")
                else:
                    # Calculate the maximum protein scale factor
                    size_factor = pdbm.check_max_size(preset_file, world_max=320)
                    size_factor = str(round(size_factor, 2))
                    sg.popup("The maximum protein scale is: " + size_factor + "x")

        # If the user selects a new PDB file, open the file selection window
        if event == "Select PDB file":
            pdb_file = sg.popup_get_file("Select PDB file")
            good_pdb = False

            # Save the pdb_file path to config
            with open(variables.config_path, "r+") as f:
                config = json.load(f)
                config["pdb_file"] = pdb_file
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()
            # check if pdb_file contains a string
            if type(pdb_file) == str:
                # check if the model is small enough for minecraft
                if not pdbm.check_model_size(pdb_file, world_max=320):
                    sg.popup("Model may be too large for Minecraft.")
                else:
                    # Calculate the maximum protein scale factor
                    size_factor = pdbm.check_max_size(pdb_file, world_max=320)
                    size_factor = str(round(size_factor, 2))
                    sg.popup("The maximum protein scale is: " + size_factor + "x")

        # Open the save folder for the user to select a save directory
        if event == "Select Minecraft Save":
            home_dir = os.path.expanduser("~")
            appdata_dir = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")
            good_dir = False

            save_path = ""
            while not good_dir:
                save_path = sg.popup_get_folder("Select your Minecraft save file", initial_folder=appdata_dir)

                # check if save_path has structure .minecraft/saves/<save_name>
                if save_path:
                    if os.path.basename(os.path.dirname(save_path)) == "saves":
                        good_dir = True
                    else:
                        sg.popup("You didn't select a Minecraft save file! Try again!")

            directory_path = os.path.join(save_path, "datapacks/mcPDB/data/protein/functions")

            if not os.path.exists(directory_path):
                os.makedirs(directory_path)

            # check for pack.mcmeta in the /datapacks/mcPDB folder and if not copy it from the python directory
            if not os.path.isfile(os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta")):
                shutil.copyfile("pack.mcmeta", os.path.join(save_path, "datapacks/mcPDB/pack.mcmeta"))

            # Save the save_path to config
            with open(variables.config_path, "r+") as f:
                config = json.load(f)
                config["save_path"] = directory_path
                f.seek(0)
                json.dump(config, f, indent=4)
                f.truncate()

        # If the user selects the "Create Minecraft Functions" button, execute the code
        if event == "Create Minecraft Functions":

            # Execute further code here
            if config["save_path"] and config["pdb_file"]:
                # Save the window variables to config
                with open(variables.config_path, "r+") as f:

                    config = json.load(f)
                    config["scale"] = float(values["scale"])
                    if values.get("mode") != "Space Filling":
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
                    config["simple"] = values.get("simple")
                    config["show_atoms"] = values.get("show_atoms")
                    config["show_hetatm"] = values.get("show_hetatm")
                    config["mesh"] = values.get("mesh")
                    f.seek(0)
                    json.dump(config, f, indent=4, default=None)
                    f.truncate()

                f = open(variables.config_path)
                config_data = json.load(f)

                f.close()

                # Read in the PDB file and process it
                pdb_file = config_data['pdb_file']
                pdb_df = pdbm.read_pdb(pdb_file)
                pdb_name = pdbm.get_pdb_code(pdb_file)
                scalar = config_data['scale']
                scaled = pdbm.scale_coordinates(pdb_df, scalar)
                moved = pdbm.move_coordinates(scaled)
                moved = pdbm.rotate_to_y(moved)
                rounded = pdbm.round_df(moved)
                #print(rounded.tail(n=25))

                # Check if the user wants het-atoms, if so, process them
                if config_data["show_hetatm"] == True:

                    #check if the first column of rounded contains any "HETATM" values

                    if "HETATM" in rounded.iloc[:, 0].values:
                        hetatm_bonds = pdbm.process_hetatom(rounded, pdb_file)
                        hetatom_df = pdbm.filter_type_atom(rounded, remove_type="ATOM", remove_atom="H")
                        #hetatom_df = pdbm.filter_type_atom(rounded, remove_type="ATOM")
                    else:
                        hetatm_bonds = None
                        hetatom_df = None
                        config_data["show_hetatm"] = False

                atom_df = pdbm.filter_type_atom(rounded, remove_type="HETATM", remove_atom="H")

                # Delete the old mcfunctions if they match the current one
                mc_dir = config_data['save_path']
                mcf.delete_mcfunctions(mc_dir, "z"+pdb_name.lower())

                # set some important parameters
                if config_data["mode"] != "Default":
                    config_data = pdbm.change_mode(config_data)

                match config_data["mode"]:
                    case "Custom":
                        custom.run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
                    case "Skeleton":
                        skeleton.run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
                    case "Space Filling":
                        space_filling.run_mode(config_data, pdb_name, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
                    case "X-ray":
                        xray.run_mode(config_data, pdb_name, pdb_file, rounded, mc_dir, atom_df, hetatom_df, hetatm_bonds)
                    case "Amino Acids":
                        amino_acids.run_mode(rounded, config_data, pdb_name, mc_dir)
                    case "Ribbon":
                        ribbon.run_mode(pdb_name, pdb_file, rounded, mc_dir, config_data, hetatom_df, hetatm_bonds)

                mcfiles = mcf.find_mcfunctions(mc_dir, pdb_name.lower())

                print(config_data["simple"])
                if config_data["simple"]:
                    mcf.create_simple_function(pdb_name, mc_dir)
                    mcf.create_clear_function(mc_dir, pdb_name)
                    mcf.delete_mcfunctions(mc_dir, "z"+pdb_name.lower())
                else:
                    mcf.create_master_function(mcfiles, pdb_name, mc_dir)
                    mcf.create_clear_function(mc_dir, pdb_name)

                lower = pdb_name.lower()
                message = f"Finished!\nRemember to /reload in your world and /function protein:build_{lower}"
                sg.popup(message)
            else:
                sg.Popup("You are missing a PDB file and/or a save directory!", title="Warning!")

    # Close the window
    window.close()
