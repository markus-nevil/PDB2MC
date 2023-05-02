from pdb_manipulation import *
from plotting_functions import *
from minecraft_functions import *
import PySimpleGUI as sg
from variables import *
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
            "mesh": False,
            "pdb_file": "",
            "save_path": ""
        }
        with open("config.json", "w") as f:
            json.dump(config, f)

    # Create the window
    window = sg.Window("My Window", open_layout)

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

        if event == "Calculate":
            # Execute further code here
            print("It's working!")

            ## actual code goes here

            # Save the window variables to config.json
            with open("config.json", "r+") as f:
                print(values)
                config = json.load(f)
                config["scale"] = float(values["scale"])
                config["atom_scale"] = float(values["atom_scale"])
                config["atoms"]["C"] = values["C"]
                config["atoms"]["N"] = values["N"]
                config["atoms"]["O"] = values["O"]
                config["atoms"]["S"] = values["S"]
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
            #print(pdb_df.head(n=20))
            #print(pdb_df.tail(n=20))

            pdb_name = get_pdb_code(pdb_file)

            scalar = config_data['scale']
            #clipped = clip_coords(pdb_df)
            #print(pdb_df.head(n=40))
            #print(clipped.head(n=40))
            #scaled = scale_coordinates(clipped, scalar)
            print(pdb_df.head(n=5))
            scaled = scale_coordinates(pdb_df, scalar)
            print(scaled.head(n=5))
            moved = move_coordinates(scaled)
            print(moved.head(n=5))
            rounded = round_df(moved)
            print(rounded.head(n=5))



            mc_dir = config_data['save_path']

            hetatm = process_hetatom(rounded, pdb_file)
            print(hetatm)

            #Check if printing a special case
            if config_data["mode"] == "Amino Acids":
                print("Amino acid mode")

            #Otherwise print a normal model
            else:
                if config_data["backbone"] == True:
                    pdb_backbone = pdb_name + "_backbone"
                    backbone = atom_subset(rounded, ['C', 'N', 'CA'], include=True)
                    intermediate = find_intermediate_points(backbone)
                    create_minecraft_functions(intermediate, pdb_backbone, False, mc_dir, config_data['atoms'])

                if config_data["sidechain"] == True:
                    branches = sidechain(rounded)
                    pdb_sidechain = pdb_name + "_sidechain"
                    create_minecraft_functions(branches, pdb_sidechain, False, mc_dir, config_data['atoms'])

                if config_data["show_atoms"] == True:
                    pdb_atoms = pdb_name + "_atoms"
                    coord = rasterized_sphere(config_data['atom_scale'])
                    center = sphere_center(config_data['atom_scale'])
                    shortened = shorten_atom_names(rounded)
                    spheres = add_sphere_coordinates(coord, center, shortened, mesh=config_data['mesh'])
                    create_minecraft_functions(spheres, pdb_atoms, False, mc_dir, config_data['atoms'])



            pdb_hetatm = pdb_name + "_hetatm"
            create_minecraft_functions(hetatm, pdb_hetatm, False, mc_dir, config_data['atoms'])

            mcfiles = find_mcfunctions(mc_dir, pdb_name.lower())
            print(mcfiles)
            print(config_data)

            create_master_function(mcfiles, pdb_name, mc_dir)

            sg.popup("Finished! Remember to /reload in your world and /function protein:drop_###")



    # Close the window
    window.close()






    #mc_backbone = create_minecraft_functions(intermediate)
    #mc_atoms = create_minecraft_functions(spheres)

    #print(mc_backbone.head(20))
    #print(mc_atoms.head(20))

    #combined = pd.concat([spheres.head(1500), intermediate.head(300), branches.head(500)])
    #combined = combined.reset_index(drop=True)
    #print(combined.head(20))
    #print(combined.tail(20))

    #plot_3d_coordinates(clip_coords(combined), 2300)
    #plot_3d_coordinates(clip_coords(spheres), 1900)
    #plot_cube(spheres, 300)

