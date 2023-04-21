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

    # Define the layout of the window
    layout = [
        [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_concrete")],
        [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
        [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_concrete")],
        [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_concrete")],
        [sg.Text("Select backbone atom"),
         sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
        [sg.Text("Select side chain atom"),
         sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
        [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
        [sg.Text("Select mode"),
         sg.DropDown(["Default", "Backbone", "Skeleton", "Space Filling", "X-ray", "X-ray Backbone", "Max", "Min"],
                     key="mode", default_value="Default")],
        [sg.Checkbox("Backbone", default=True, key="backbone"),
         sg.Checkbox("Sidechain", default=True, key="sidechain"),
         sg.Checkbox("Mesh-style atoms", default =  False, key="mesh")],
        [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale")],
        [sg.Text("Atom scale"), sg.Input(default_text='1.5', key="atom_scale")],
        [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
        [sg.Button("Calculate", bind_return_key=True)]
    ]

    # Create the window
    window = sg.Window("My Window", layout)

    # Loop to keep the window open
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED:
            break

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
                config["mode"] = values["mode"]
                config["backbone"] = values["backbone"]
                config["sidechain"] = values["sidechain"]
                config["mesh"] = values["mesh"]
                f.seek(0)
                json.dump(config, f, indent=4)
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

            #hetatm = process_hetatom(rounded)



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

            #pdb_hetatm = pdb_name + "_hetatm"
            #create_minecraft_functions(hetatm, pdb_hetatm, False, mc_dir, config_data['atoms'])

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

