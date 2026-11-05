"""Default colours and settings of every mode, shared by the mode windows and the command line."""
import copy

from PDB2MC.build import DEFAULT_CHAIN_BLOCKS
from PDB2MC.space_filling import SASA_radius

MODES =["Custom", "Skeleton", "X-Ray", "Space Filling", "Ribbon", "Amino Acids"]

# Fixed atom colours used where a mode has no colour choice for them
BASE_ATOMS = {
    'O': 'red_wool',
    'N': 'blue_wool',
    'P': 'lime_wool',
    'S': 'yellow_wool',
    'C': 'black_wool',
    'FE': 'iron_block',
}

CONCRETE_ELEMENTS = {'C': 'black_concrete', 'O': 'red_concrete', 'N': 'blue_concrete',
                     'S': 'yellow_concrete', 'P': 'lime_concrete', 'other_atom': 'pink_concrete'}
GLASS_ELEMENTS = {'C': 'black_stained_glass', 'O': 'red_stained_glass', 'N': 'blue_stained_glass',
                  'S': 'yellow_stained_glass', 'P': 'lime_stained_glass', 'other_atom': 'pink_stained_glass'}

AMINO_ACIDS = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE",
               "LEU", "LYS", "MET", "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL"]
AMINO_ACID_NAMES = {
    "ALA": "Alanine", "ARG": "Arginine", "ASN": "Asparagine", "ASP": "Aspartate", "CYS": "Cysteine",
    "GLN": "Glutamine", "GLU": "Glutamate", "GLY": "Glycine", "HIS": "Histidine", "ILE": "Isoleucine",
    "LEU": "Leucine", "LYS": "Lysine", "MET": "Methionine", "PHE": "Phenylalanine", "PRO": "Proline",
    "SER": "Serine", "THR": "Threonine", "TRP": "Tryptophan", "TYR": "Tyrosine", "VAL": "Valine",
}

# Colour styles of the Amino Acids mode
AMINO_ACID_STYLES = {
    "Residue": {
        "ALA": "red_concrete", "ARG": "yellow_concrete", "ASN": "cyan_concrete", "ASP": "purple_concrete",
        "CYS": "brown_concrete", "GLN": "light_gray_concrete", "GLU": "orange_glazed_terracotta",
        "GLY": "green_glazed_terracotta", "HIS": "blue_glazed_terracotta", "ILE": "pink_glazed_terracotta",
        "LEU": "gray_glazed_terracotta", "LYS": "red_terracotta", "MET": "lime_terracotta",
        "PHE": "light_blue_terracotta", "PRO": "magenta_terracotta", "SER": "magenta_wool",
        "THR": "black_wool", "TRP": "orange_stained_glass", "TYR": "green_stained_glass",
        "VAL": "purple_stained_glass",
    },
    "Type": {
        "ALA": "green_wool", "ARG": "red_wool", "ASN": "blue_wool", "ASP": "blue_wool", "CYS": "orange_wool",
        "GLN": "yellow_wool", "GLU": "blue_wool", "GLY": "orange_wool", "HIS": "red_wool", "ILE": "green_wool",
        "LEU": "green_wool", "LYS": "red_wool", "MET": "green_wool", "PHE": "green_wool", "PRO": "orange_wool",
        "SER": "yellow_wool", "THR": "yellow_wool", "TRP": "green_wool", "TYR": "green_wool",
        "VAL": "green_wool",
    },
    "Charge": {
        "ALA": "pearlescent_froglight", "ARG": "emerald_block", "ASN": "end_stone", "ASP": "cobblestone",
        "CYS": "cherry_leaves", "GLN": "end_stone_bricks", "GLU": "light_gray_wool", "GLY": "snow_block",
        "HIS": "white_glazed_terracotta", "ILE": "red_mushroom_block", "LEU": "pink_wool",
        "LYS": "weathered_copper", "MET": "ochre_froglight", "PHE": "cherry_planks",
        "PRO": "verdant_froglight", "SER": "snow_block", "THR": "snow_block", "TRP": "snow_block",
        "TYR": "white_wool", "VAL": "pink_concrete",
    },
    "Hydrophobicity": {
        "ALA": "snow_block", "ARG": "copper_block", "ASN": "quartz_block", "ASP": "nether_wart_block",
        "CYS": "diorite", "GLN": "stripped_cherry_log", "GLU": "red_wool", "GLY": "snow_block",
        "HIS": "pink_concrete", "ILE": "light_gray_glazed_terracotta", "LEU": "packed_ice",
        "LYS": "red_mushroom_block", "MET": "white_shulker_box", "PHE": "tube_coral_block",
        "PRO": "cherry_planks", "SER": "snow_block", "THR": "snow_block", "TRP": "blue_concrete",
        "TYR": "blue_ice", "VAL": "snow_block",
    },
"Size": {
    # tiny (<100 Å^3)
    "GLY": "white_wool",
    "ALA": "white_wool",
    "SER": "white_wool",

    # small (100-130)
    "CYS": "light_blue_wool",
    "ASP": "light_blue_wool",
    "PRO": "light_blue_wool",
    "ASN": "light_blue_wool",
    "THR": "light_blue_wool",

    # medium (130-160)
    "GLU": "cyan_wool",
    "VAL": "cyan_wool",
    "GLN": "cyan_wool",
    "HIS": "cyan_wool",

    # large (160-180)
    "MET": "blue_wool",
    "ILE": "blue_wool",
    "LEU": "blue_wool",
    "LYS": "blue_wool",
    "ARG": "blue_wool",

    # very large (>180)
    "PHE": "purple_wool",
    "TYR": "purple_wool",
    "TRP": "purple_wool",
},
}

# Metal ions: element symbol as it appears in structure files -> (name, default block). Every mode colours a
# metal with this block (Tools > Metal Ion Settings overrides it, see user_settings.metal_blocks).
METAL_IONS = {
    "LI": ("Lithium", "red_concrete"),
    "NA": ("Sodium", "yellow_concrete"),
    "K": ("Potassium", "purple_concrete"),
    "RB": ("Rubidium", "magenta_concrete"),
    "CS": ("Cesium", "orange_concrete"),
    "MG": ("Magnesium", "lime_concrete"),
    "CA": ("Calcium", "calcite"),
    "SR": ("Strontium", "red_wool"),
    "BA": ("Barium", "lime_wool"),
    "AL": ("Aluminium", "light_gray_concrete"),
    "V": ("Vanadium", "cyan_concrete"),
    "CR": ("Chromium", "green_concrete"),
    "MN": ("Manganese", "amethyst_block"),
    "FE": ("Iron", "iron_block"),
    "CO": ("Cobalt", "lapis_block"),
    "NI": ("Nickel", "emerald_block"),
    "CU": ("Copper", "copper_block"),
    "ZN": ("Zinc", "prismarine"),
    "MO": ("Molybdenum", "coal_block"),
    "CD": ("Cadmium", "yellow_glazed_terracotta"),
    "W": ("Tungsten", "netherite_block"),
    "PT": ("Platinum", "quartz_block"),
    "AU": ("Gold", "gold_block"),
    "AG": ("Silver", "diamond_block"),
    "HG": ("Mercury", "redstone_block"),
    "PB": ("Lead", "gray_concrete"),
}


def default_metal_blocks():
    return {metal: block for metal, (_, block) in METAL_IONS.items()}


_COMMON = {
    'backbone_size': 1.0,
    'atom_scale': 1.5,
    'scale': 1.0,
    'show_atoms': True,
    'show_hetatm': True,
    'mesh': False,
    'backbone': True,
    'sidechain': True,
    'by_chain': False,
    'simple': True,
    'bar_style': False,
    'chain_blocks': list(DEFAULT_CHAIN_BLOCKS),
    'residue_mods': {},
    'color_scheme': 'Chain',
}


def default_config(mode):
    """Build settings of a mode as its window starts out (without pdb_file / save_path)."""
    config = copy.deepcopy(_COMMON)
    atoms = dict(BASE_ATOMS, **default_metal_blocks(), other_atom='pink_concrete', backbone_atom='gray_concrete',
                 sidechain_atom='gray_concrete')
    if mode == "Custom":
        atoms.update(CONCRETE_ELEMENTS)
    elif mode == "X-Ray":
        atoms.update(GLASS_ELEMENTS)
    elif mode == "Space Filling":
        atoms.update(CONCRETE_ELEMENTS)
        config.update(atom_scale=1.0, sasa_radius=SASA_radius)
    elif mode == "Ribbon":
        atoms['ribbon_atom'] = 'red_concrete'
        config.update(sidechain=False, by_chain=True)
    elif mode == "Amino Acids":
        config.update(sidechain=False, color_style="Residue",
                      amino_acids=dict(AMINO_ACID_STYLES["Residue"]))
    elif mode != "Skeleton":
        raise ValueError(f"Unknown mode: {mode}")
    config['atoms'] = atoms
    return config
