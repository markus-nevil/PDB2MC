"""
All tool tip text of PDB2MC, in one place. Edit the text here; no other file needs to change.

Each entry is  widget name: text.  OPTIONS covers the mode windows; MODE_OPTIONS replaces an entry for one
mode where the same option does something else there. The remaining sections cover the other windows.
Long tips are wrapped automatically, so keep each one on a single string.
"""
import textwrap

WRAP_WIDTH = 60


# --- options in the mode windows ---

OPTIONS = {
    # Atom colours (Custom, X-Ray, Space Filling)
    "cColorBox": "Block for carbon atoms.",
    "oColorBox": "Block for oxygen atoms.",
    "nColorBox": "Block for nitrogen atoms.",
    "sColorBox": "Block for sulfur atoms.",
    "pColorBox": "Block for phosphorus atoms.",
    "otherColorBox": "Block for every other element, such as selenium or chlorine. Metal ions have their "
                     "own blocks: see Tools > Metal Ion Settings.",

    # Showing and hiding
    "showAtomsCheck": "Show the atoms of the proteins and nucleic acids as spheres.",
    "otherMoleculeCheck": "Show molecules that are not protein, DNA or RNA, such as ligands, ions and cofactors.",
    "meshCheck": "Draw hollow atoms made of a thin mesh. Uses far fewer blocks, so the model builds faster "
                 "and the backbone shows through.",
    "showBackboneCheck": "Show the N-C-C backbone of the proteins and the sugar-phosphate backbone of DNA and RNA.",
    "showSidechainCheck": "Show the amino acid side chains (R-groups) and the nucleotide bases.",

    # Colours of the skeleton
    "backboneColorBox": "Block for the backbone. Not used while the model is coloured by chain.",
    "sidechainColorBox": "Block for the side chains. Not used while the model is coloured by chain.",
    "colorByChainCheck": "Colour the backbone and side chains by the colour scheme below instead of one colour. "
                         "Ticking this with the Chain or Molecule scheme opens the list of chain colours; the list "
                         "repeats when a model has more chains than colours.",
    "colorSchemeBox": "Chain: each chain its own colour. Molecule: every copy of the same protein or nucleic acid "
                      "the same colour. Hydrophobicity: blue residues like water, orange ones avoid it. Charge: "
                      "positive blue, negative red (DNA and RNA are negative). Confidence: blue where the "
                      "structure is most sure of the atom positions, orange where it is least sure (B-factor, or "
                      "pLDDT for AlphaFold models). The blocks are set in PDB2MC/color_schemes.py.",

    # Sizes
    "aScaleSpinBox": "Diameter of each atom in blocks, rounded up.",
    "backboneScaleSpinBox": "Width of the backbone in blocks.",
    "pScaleSpinBox": "Enlarge the whole model by this factor. Selecting a structure sets this to the largest "
                     "whole number that still fits in the Minecraft world.",

    # Ribbon
    "ribbonColorBox": "Block for the ribbons. Not used while the model is coloured by chain.",
    "barStyleCheck": "Draw alpha helices as straight rods instead of spiraling ribbons.",

    # Amino Acids
    "colorStyleBox": "Fill in all 20 residue colours from a preset: one colour per residue, or colours by "
                     "residue type, charge, hydrophobicity or size. The colours can still be changed afterwards.",

    # Space Filling
    "sasaRadiusSpinBox": "Radius in angstroms of the probe ball rolled over the atoms to find the surface. "
                         "1.4 is a water molecule. Larger values give a smoother surface that hides small "
                         "grooves; 0 gives the plain van der Waals surface.",

    # Shared by every mode
    "modelNameEdit": "Name of the model in Minecraft, as in /function protein:build_<name> and "
                     "/trigger build_<name>. Filled in with the PDB ID when a structure is selected. "
                     "Letters, numbers, dots and dashes; anything else becomes a dash.",
    "selectPDBFileButton": "Choose a .pdb, .cif or .mmcif structure file. Tools > Default PDB/CIF Folder sets "
                           "where this starts.",
    "selectIncludedPDBButton": "Choose one of the example structures that come with PDB2MC.",
    "pdbIdButton": "Type a PDB ID, such as 1GFL, to download that structure from the RCSB Protein Data Bank "
                   "(needs an internet connection). Find IDs at rcsb.org.",
    "selectMinecraftSaveButton": "Choose the Minecraft world the model is added to.",
    "simpleOutputCheck": "Make one command that builds the whole model. Untick to get a separate command for "
                         "each part of the model.",
    "modifyResiduesButton": "Give selected residues their own block, or hide them.",
    "previewButton": "See the model turning, coloured with these settings, and how big it will be in Minecraft "
                     "at this protein scale.",
    "createFunctionsButton": "Build the model and add it to the selected Minecraft world.",
}

# Options that mean something else in one mode
MODE_OPTIONS = {
    "Space Filling": {
        "colorByChainCheck": "Colour the surface by the colour scheme below instead of by element. Ticking this "
                             "with the Chain or Molecule scheme opens the list of chain colours.",
        "meshCheck": "Place only some of the surface blocks, so the skeleton inside shows through.",
        "otherColorBox": "Block for surface atoms of every other element.",
    },
    "Ribbon": {
        "colorByChainCheck": "Colour the ribbons and backbone by the colour scheme below instead of one colour. "
                             "Ticking this with the Chain or Molecule scheme opens the list of chain colours.",
        "showBackboneCheck": "Show the backbone between the ribbons.",
        "aScaleSpinBox": "Diameter in blocks, rounded up, of the atoms of other molecules.",
    },
    "Skeleton": {
        "otherColorBox": "Block for the atoms of other molecules, for every element without its own colour.",
        "aScaleSpinBox": "Diameter in blocks, rounded up, of the atoms of other molecules.",
    },
    "Amino Acids": {
        "aScaleSpinBox": "Diameter of each residue sphere in blocks, rounded up.",
    },
}

# Colour of each residue in Amino Acids mode, with what makes the residue stand out
RESIDUES = {
    "ALA": "Alanine (Ala, A): small and hydrophobic.",
    "ARG": "Arginine (Arg, R): large and positively charged.",
    "ASN": "Asparagine (Asn, N): polar and uncharged.",
    "ASP": "Aspartate (Asp, D): negatively charged.",
    "CYS": "Cysteine (Cys, C): contains sulfur and can form disulfide bonds.",
    "GLN": "Glutamine (Gln, Q): polar and uncharged.",
    "GLU": "Glutamate (Glu, E): negatively charged.",
    "GLY": "Glycine (Gly, G): the smallest residue, with no side chain.",
    "HIS": "Histidine (His, H): aromatic and can carry a positive charge.",
    "ILE": "Isoleucine (Ile, I): hydrophobic.",
    "LEU": "Leucine (Leu, L): hydrophobic.",
    "LYS": "Lysine (Lys, K): positively charged.",
    "MET": "Methionine (Met, M): hydrophobic and contains sulfur.",
    "PHE": "Phenylalanine (Phe, F): aromatic and hydrophobic.",
    "PRO": "Proline (Pro, P): its ring puts a bend in the backbone.",
    "SER": "Serine (Ser, S): small and polar.",
    "THR": "Threonine (Thr, T): polar.",
    "TRP": "Tryptophan (Trp, W): the largest residue, aromatic.",
    "TYR": "Tyrosine (Tyr, Y): aromatic and polar.",
    "VAL": "Valine (Val, V): hydrophobic.",
}
RESIDUE_TEMPLATE = "Block for this residue. {residue}"


# --- other windows ---

SELECTION_LABELS = {
    "selectedPDBLabel": "The selected structure file.",
    "selectedMinecraftLabel": "The selected Minecraft world.",
}

SIDEBAR = {
    "Custom": "Atoms as spheres on a skeleton, with a colour for each element.",
    "Skeleton": "Only the backbone and side chains, the lightest model.",
    "X-Ray": "Custom mode with see-through glass atoms, so the backbone shows inside.",
    "Space Filling": "The solid outer surface of the molecule.",
    "Amino Acids": "One sphere per residue, coloured by residue type.",
    "Ribbon": "Helices and sheets as ribbons.",
    "Help": "Open the PDB2MC instructions.",
    "Github": "Open the PDB2MC project page in a web browser.",
    "Tools": "Settings and tools for your Minecraft worlds.",
    "RCSB.org": "Open the RCSB Protein Data Bank in a web browser to find structures.",
}

MAIN_WINDOW = {
    "comboBox": "Choose how the model is drawn in Minecraft.",
    "help": "Open the PDB2MC instructions.",
}

TOOLS = {
    "metalIonSettings": "Choose the block for each metal ion, for all modes. Saved for next time.",
    "defaultFolder": "Choose the folder the Select PDB File button starts in. Saved for next time.",
    "removeFunctionFiles": "Delete every PDB2MC model file from a Minecraft world. Models already built in "
                           "the world stay there.",
    "openFunctionDir": "Open the folder of the selected world that holds the model commands.",
    "openIncludedDir": "Open the folder with the example structures.",
    "movePreset": "Copy the empty PDB2MC world into your Minecraft saves.",
}

METAL_DIALOG = {
    "metalBlock": "Block for {name} ions in every mode.",
    "reset": "Restore the block PDB2MC starts with for every metal ion.",
}

FOLDER_DIALOG = {
    "path": "The folder the Select PDB File button starts in.",
    "browse": "Choose the folder.",
    "clear": "Forget the folder, so the file window opens where Windows chooses.",
}

CHAIN_DIALOG = {
    "list": "Chain 1 uses the first block, chain 2 the second, and so on. Drag to reorder.",
    "entry": "Type a block name, or several separated by commas.",
    "add": "Add the typed block to the end of the list.",
    "up": "Move the selected blocks up the list.",
    "down": "Move the selected blocks down the list.",
    "remove": "Remove the selected blocks from the list.",
    "reset": "Restore the preset chain colours.",
}

RESIDUE_POPUP = {
    "block": "Give the selected residues their own block.",
    "hide": "Leave the selected residues out of the model.",
    "clear": "Undo the changes of the selected residues (of all residues when none are selected).",
    "okay": "Keep these changes and close this window.",
    "residue": "True residue id: {resid}",
}


def wrapped(text):
    """Text broken into lines: Qt does not wrap plain text tool tips by itself."""
    return textwrap.fill(text, WRAP_WIDTH, break_long_words=False, break_on_hyphens=False)


def option(name, mode=None):
    """Tool tip of an option or shared control of a mode window."""
    code = name.removesuffix("ColorBox").upper()
    if code in RESIDUES:
        return residue(code)
    return wrapped(MODE_OPTIONS.get(mode, {}).get(name) or OPTIONS.get(name, ""))


def residue(code):
    return wrapped(RESIDUE_TEMPLATE.format(residue=RESIDUES[code]))


def tip(section, key, **values):
    """Tool tip from one of the other sections, e.g. tip(tooltips.TOOLS, "movePreset")."""
    return wrapped(section[key].format(**values))
