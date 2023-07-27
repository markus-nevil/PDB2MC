import PySimpleGUI as sg

config_path = "docs/config.json"

decorative_blocks = [
    'acacia_log', 'andesite', 'birch_log', 'blackstone', 'blue_ice', 'bone_block', 'brick_block',
    'chiseled_quartz_block', 'chiseled_red_sandstone', 'chiseled_sandstone', 'chiseled_stone_bricks',
    'clay', 'coal_block', 'cobblestone', 'cracked_stone_bricks', 'cut_red_sandstone', 'cut_sandstone',
    'dark_oak_log', 'diamond_block', 'diorite', 'end_stone_bricks', 'glowstone', 'gold_block', 'granite',
    'gray_concrete', 'gray_terracotta', 'gray_wool', 'green_concrete', 'green_terracotta', 'green_wool',
    'honeycomb_block', 'iron_block', 'jungle_log', 'lapis_block', 'light_blue_concrete', 'light_blue_wool',
    'light_gray_concrete', 'light_gray_wool', 'lime_concrete', 'lime_wool', 'magenta_concrete',
    'magenta_wool', 'nether_bricks', 'oak_log', 'obsidian', 'orange_concrete', 'orange_terracotta',
    'pink_concrete', 'pink_terracotta', 'polished_andesite', 'polished_blackstone', 'polished_diorite',
    'polished_granite', 'prismarine', 'prismarine_bricks', 'purpur_block', 'quartz_block',
    'red_concrete', 'red_sandstone', 'red_terracotta', 'sandstone', 'smooth_quartz', 'smooth_red_sandstone',
    'smooth_sandstone', 'smooth_stone', 'snow_block', 'spruce_log', 'stone', 'stone_bricks', 'stripped_acacia_log',
    'stripped_birch_log', 'stripped_dark_oak_log', 'stripped_jungle_log', 'stripped_oak_log', 'stripped_spruce_log',
    'terracotta', 'warped_stem', 'white_concrete', 'white_terracotta', 'white_wool', 'yellow_concrete',
    'yellow_terracotta', 'white_stained_glass', 'orange_stained_glass', 'magenta_stained_glass',
    'light_blue_stained_glass', 'yellow_stained_glass', 'lime_stained_glass',
    'pink_stained_glass', 'gray_stained_glass', 'light_gray_stained_glass', 'cyan_stained_glass', 'purple_stained_glass',
    'blue_stained_glass', 'brown_stained_glass', 'green_stained_glass', 'red_stained_glass', 'black_stained_glass'
]

#decorative_blocks = ["andesite",    "bedrock",    "blackstone",    "blackstone_bricks",    "brick",    "chiseled_nether_bricks",    "chiseled_polished_blackstone",    "cobblestone",    "cracked_nether_bricks",    "cracked_polished_blackstone_bricks",    "cut_red_sandstone",    "cut_sandstone",    "diorite",    "end_stone_bricks",    "gilded_blackstone",    "glowstone",    "granite",    "gravel",    "infested_chiseled_stone_bricks",    "infested_cobblestone",    "infested_cracked_stone_bricks",    "infested_mossy_stone_bricks",    "infested_stone",    "infested_stone_bricks",    "mossy_cobblestone",    "mossy_stone_bricks",    "nether_bricks",    "nether_gold_ore",    "nether_quartz_ore",    "obsidian",    "polished_andesite",    "polished_blackstone",    "polished_blackstone_bricks",    "polished_diorite",    "polished_granite",    "red_nether_bricks",    "red_sandstone",    "sandstone",    "smooth_quartz",    "smooth_red_sandstone",    "smooth_sandstone",    "soul_sand",    "soul_soil",    "stone",    "stone_bricks",    "terracotta",    "white_wool",    "orange_wool",    "magenta_wool",    "light_blue_wool",    "yellow_wool",    "lime_wool",    "pink_wool",    "gray_wool",    "light_gray_wool",    "cyan_wool",    "purple_wool",    "blue_wool",    "brown_wool",    "green_wool",    "red_wool",    "black_wool",    "grass_block",    "mycelium",    "podzol"]
concrete_blocks = [  "black_concrete",    "blue_concrete",    "brown_concrete",    "cyan_concrete",    "gray_concrete",    "green_concrete",    "light_blue_concrete",    "lime_concrete",    "magenta_concrete",    "orange_concrete",    "pink_concrete",    "purple_concrete",    "red_concrete",    "white_concrete",    "yellow_concrete"]


block_colors = {(143, 61, 46), (224, 97, 0), (57, 42, 35), (218, 224, 162), (186, 99, 29), (42, 35, 40), (76, 83, 42),
                (188, 188, 188), (169, 48, 159), (216, 202, 155), (152, 94, 67), (99, 171, 158), (119, 118, 119),
                (30, 67, 140), (216, 215, 210), (233, 236, 236), (192, 193, 194), (99, 156, 151), (216, 203, 155),
                (58, 175, 217), (73, 91, 36), (127, 127, 127), (94, 168, 24), (16, 15, 15), (58, 58, 77),
                (142, 142, 134), (229, 148, 29), (112, 185, 25), (189, 101, 31), (171, 131, 84), (169, 125, 169),
                (217, 206, 159), (84, 109, 27), (62, 68, 71), (158, 158, 158), (149, 103, 85), (85, 67, 25),
                (122, 121, 122), (246, 208, 61), (125, 125, 125), (132, 134, 133), (0, 0, 3), (209, 178, 161),
                (171, 132, 84), (109, 85, 50), (96, 76, 49), (35, 137, 198), (213, 101, 142), (207, 213, 214),
                (125, 125, 115), (196, 176, 118), (231, 226, 218), (160, 166, 179), (177, 144, 86), (53, 48, 56),
                (118, 117, 118), (240, 175, 21), (15, 10, 24), (161, 83, 37), (103, 96, 86), (161, 78, 78),
                (186, 133, 35), (174, 92, 59), (154, 106, 89), (183, 96, 27), (115, 89, 52), (58, 37, 16), (60, 46, 26),
                (142, 32, 32), (116, 167, 253), (189, 68, 179), (136, 136, 136), (220, 220, 220), (98, 237, 228),
                (54, 57, 61)}

chain_blocks = {"1" : "red_wool",
                "2" : "blue_wool",
                "3" : "yellow_wool",
                "4" : "lime_wool",
                "5" : "pink_wool",
                "6" : "light_gray_wool",
                "7" : "purple_wool",
                "8" : "light_blue_wool",
                "9" : "green_wool",
                "10": "orange_wool"}

# Define the layout of the window
open_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="")],
    [sg.Button('Switch Layout')]
]

presets = {"Buckyball": "buckyball.pdb",
           "Alanine": "ala.pdb",
           "Glucose": "glucose.pdb"}

preset_layout = [
    [sg.Text("Select pre-made models")],
    [sg.Listbox(presets, size=(20,5), key="preset")],
    [sg.Button('OK')]
]


# Custom Mode
default_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="Custom"),
    sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_concrete")],
    [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
    [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_concrete")],
    [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_concrete")],
    [sg.Text("Select P atom"), sg.DropDown(decorative_blocks, key="P", default_value="lime_concrete")],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete"),
    sg.Text("Select side chain atom"),
     sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Checkbox("Color the backbone by chain?", default= False, key="by_chain")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Checkbox("Show Atoms", default=True, key="show_atoms"),
     sg.Checkbox("Show Hetatoms", default=True, key="show_hetatm")],
    [sg.Checkbox("Show Backbone", default=True, key="backbone"),
     sg.Input(default_text='1.0', key="backbone_size", size=(20, 5))],
    [sg.Checkbox("Show Sidechain", default=True, key="sidechain"),
     sg.Checkbox("Mesh-style atoms", default=False, key="mesh")],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale", size=(20,5)), sg.Text("Atom scale"), sg.Input(default_text='1.5', key="atom_scale", size=(20,5))],
    [sg.Button("Select PDB file"), sg.Text("or"), sg.Button("Select Included PDB file"), sg.Text("and"), sg.Button("Select Minecraft Save")],
    [sg.HorizontalSeparator()],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]

# Backbone and Skeleton
backbone_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="Skeleton"),
        sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Text("Select side chain atom"),
     sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Checkbox("Backbone", default=True, key="backbone"),
        sg.Input(default_text='1.0', key="backbone_size", size=(20, 5))],
    [sg.Checkbox("Sidechain", default=True, key="sidechain"),
     sg.Checkbox("Show Hetatoms", default=True, key="show_hetatm")],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale")],
    [sg.Text("Atom scale"), sg.Input(default_text='1.5', key="atom_scale")],
    [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]

# Space Filling
sf_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="Space Filling"),
        sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_concrete")],
    [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
    [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_concrete")],
    [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_concrete")],
    [sg.Text("Select P atom"), sg.DropDown(decorative_blocks, key="P", default_value="lime_concrete")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Checkbox("Mesh-style atoms", default=False, key="mesh"),
     sg.Checkbox("Show Atoms", default=True, key="show_atoms"),
     sg.Checkbox("Show Hetatoms", default= True, key="show_hetatm")],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale")],
    [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]

# X-ray and X-ray backbone
xray_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="X-ray"),
        sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_stained_glass")],
    [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_stained_glass")],
    [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_stained_glass")],
    [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_stained_glass")],
    [sg.Text("Select P atom"), sg.DropDown(decorative_blocks, key="P", default_value="lime_stained_glass")],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Text("Select side chain atom"),
     sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Checkbox("Backbone", default=True, key="backbone"),
        sg.Input(default_text='1.0', key="backbone_size", size=(20, 5))],
    [sg.Checkbox("Sidechain", default=True, key="sidechain"),
     sg.Checkbox("Mesh-style atoms", default=False, key="mesh"),
     sg.Checkbox("Show Atoms", default=True, key="show_atoms"),
     sg.Checkbox("Show Hetatoms", default=True, key="show_hetatm")],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale")],
    [sg.Text("Atom scale"), sg.Input(default_text='1.5', key="atom_scale")],
    [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]
# Ribbon mode
ribbon_layout = [
    [sg.Text("Select mode"),
        sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                    key="mode", default_value="Ribbon"),
        sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select Ribbon color"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Text("Select side chain atom"),
     sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Checkbox("Show Backbone", default=True, key="backbone"),
     sg.Checkbox("Sidechain", default=False, key="sidechain"),
     sg.Checkbox("Show Hetatoms", default=False, key="show_hetatm")],
    [sg.Text("Protein scale"), sg.Input(default_text='4.0', key="scale")],
    [sg.Text("Atom scale"), sg.Input(default_text='1.5', key="atom_scale")],
    [sg.Button("Select PDB file"), sg.Text("or"), sg.Button("Select Included PDB file"), sg.Text("and"), sg.Button("Select Minecraft Save")],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]
# Amino acid
aa_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Custom", "Skeleton", "X-ray", "Space Filling", "Amino Acids", "Ribbon"],
                 key="mode", default_value="Amino Acids"),
        sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select Alanine"), sg.DropDown(decorative_blocks, key="ALA", default_value="white_stained_glass")],
    [sg.Text("Select Arginine"), sg.DropDown(decorative_blocks, key="ARG", default_value="red_stained_glass")],
    [sg.Text("Select Asparagine"), sg.DropDown(decorative_blocks, key="ASN", default_value="blue_stained_glass")],
    [sg.Text("Select Aspartate"), sg.DropDown(decorative_blocks, key="ASP", default_value="black_stained_glass")],
    [sg.Text("Select Cysteine"), sg.DropDown(decorative_blocks, key="CYS", default_value="yellow_stained_glass")],
    [sg.Text("Select Glutamate"), sg.DropDown(decorative_blocks, key="GLN", default_value="obsidian")],
    [sg.Text("Select Glutamine"), sg.DropDown(decorative_blocks, key="GLU", default_value="pink_stained_glass")],
    [sg.Text("Select Glycine"), sg.DropDown(decorative_blocks, key="GLY", default_value="lime_stained_glass")],
    [sg.Text("Select Histidine"), sg.DropDown(decorative_blocks, key="HIS", default_value="green_stained_glass")],
    [sg.Text("Select Isoleucine"), sg.DropDown(decorative_blocks, key="ILE", default_value="light_blue_stained_glass")],
    [sg.Text("Select Leucine"), sg.DropDown(decorative_blocks, key="LEU", default_value="cyan_stained_glass")],
    [sg.Text("Select Lysine"), sg.DropDown(decorative_blocks, key="LYS", default_value="magenta_stained_glass")],
    [sg.Text("Select Methionine"), sg.DropDown(decorative_blocks, key="MET", default_value="purple_stained_glass")],
    [sg.Text("Select Phenylalanine"), sg.DropDown(decorative_blocks, key="PHE", default_value="brown_stained_glass")],
    [sg.Text("Select Proline"), sg.DropDown(decorative_blocks, key="PRO", default_value="gray_stained_glass")],
    [sg.Text("Select Serine"), sg.DropDown(decorative_blocks, key="SER", default_value="light_gray_stained_glass")],
    [sg.Text("Select Threonine"), sg.DropDown(decorative_blocks, key="THR", default_value="yellow_wool")],
    [sg.Text("Select Tryptophan"), sg.DropDown(decorative_blocks, key="TRP", default_value="pink_wool")],
    [sg.Text("Select Tyrosine"), sg.DropDown(decorative_blocks, key="TYR", default_value="red_wool")],
    [sg.Text("Select Valine"), sg.DropDown(decorative_blocks, key="VAL", default_value="blue_wool")],
    [sg.HorizontalSeparator()],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Checkbox("Backbone", default=True, key="backbone"),
        sg.Input(default_text='1.0', key="backbone_size", size=(20, 5))],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale", size=(20, 5)), sg.Text("Atom scale"),
     sg.Input(default_text='1.5', key="atom_scale", size=(20, 5))],
    [sg.Button("Select PDB file"), sg.Text("or"), sg.Button("Select Included PDB file"), sg.Text("and"),
     sg.Button("Select Minecraft Save")],
    [sg.HorizontalSeparator()],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]

#min max
minmax_layout = [
    [sg.Text("Select mode"),
     sg.DropDown(["Default", "Backbone", "Skeleton", "Space Filling", "X-ray", "X-ray Backbone", "Amino Acids", "Max", "Min"],
                 key="mode", default_value="Space Filling")],
    [sg.Button('Switch Layout')],
    [sg.HorizontalSeparator()],
    [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_concrete")],
    [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
    [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_concrete")],
    [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_concrete")],
    [sg.Text("Select P atom"), sg.DropDown(decorative_blocks, key="P", default_value="lime_concrete")],
    [sg.Text("Select backbone atom"),
     sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Text("Select side chain atom"),
     sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Checkbox("Backbone", default=True, key="backbone"),
     sg.Checkbox("Sidechain", default=True, key="sidechain"),
     sg.Checkbox("Mesh-style atoms", default=False, key="mesh"),
     sg.Checkbox("Show Atoms", default=True, key="show_atoms"),
     sg.Checkbox("Show Hetatoms", default= True, key="show_hetatm")],
    [sg.Text("Protein scale"), sg.Input(default_text='1.0', key="scale")],
    [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
    [sg.Button("Create Minecraft Functions", bind_return_key=True)]
]
