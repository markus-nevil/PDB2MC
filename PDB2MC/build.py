"""
Shared model building for every mode.

build_model() runs a whole build the same way for all modes: it reads the structure, puts every atom in
one block coordinate frame (prepare_coordinates), lets the mode turn atoms into block parts, and writes
the parts and the build_/clear_ functions. Because all parts of a model come from the same coordinates,
atoms, backbone, surface and HETATMs always line up.

ModelBuilder.write() also applies the user's residue modifications ("Modify Residues") and the chain
colour list to every part, so each mode gets them without extra code.
"""
import re
from collections import deque

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from PDB2MC import minecraft_functions as mcf, pdb_manipulation as pdbm, variables

# Atoms joined into the backbone line: protein N-CA-C and the nucleic acid sugar-phosphate chain
BACKBONE_ATOMS = ['C', 'N', 'CA', 'P', "O5'", "C5'", "C4'", "C3'", "O3'"]
# Backbone atoms left out of the sidechain bond search (CA, C and C4'/C3' anchor the branches)
NOT_SIDECHAIN_ATOMS = ['N', 'P', "O5'", "C5'", "O3'"]

# Default colours for "colour by chain"; chain n uses entry (n - 1) % len, so the list repeats
DEFAULT_CHAIN_BLOCKS = [variables.chain_blocks[str(i)] for i in range(1, 11)]

EMPTY_BLOCKS = pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])


def prepare_coordinates(structure, scale):
    """
    Scaled, origin-shifted, Y-rotated and rounded coordinates for a StructureData, with extra columns:
    'polymer' (protein/nucleic acid atom, including modified HETATM residues) and 'segment' (continuous
    backbone stretch id for backbone atoms, None elsewhere). Waters are removed.
    """
    df = pdbm.structure_to_df(structure)
    if df.empty:
        raise ValueError("The structure contains no atoms.")
    df = pdbm.scale_coordinates(df, scale)
    df = pdbm.move_coordinates(df)
    df = pdbm.rotate_to_y(df)

    # Chain breaks are found on the unrounded coordinates; rounding would blur bond lengths
    df['polymer'] = pdbm.polymer_atom_mask(df)
    backbone_mask = (df['polymer'] & df['atom'].isin(BACKBONE_ATOMS)).to_numpy()
    segment = pd.Series(None, index=df.index, dtype=object)
    segment[backbone_mask] = pdbm.backbone_segments(df[backbone_mask], scale=scale)
    df['segment'] = segment
    # Unrounded block coordinates, for modes that need sub-block precision (space filling)
    df[['Xf', 'Yf', 'Zf']] = df[['X', 'Y', 'Z']].to_numpy(dtype=float)
    return pdbm.round_df(df).reset_index(drop=True)


# --- chain colours ---

def chain_numbers(chains, count=10):
    """Colour number 1..count for each chain, in order of first appearance (cycling after `count` chains)."""
    return {chain: (i % count) + 1 for i, chain in enumerate(pd.unique(pd.Series(chains)))}


def dark_block(block):
    """Darker partner of a chain colour (used for the inner skeleton of space filling models)."""
    for material in ("_concrete_powder", "_concrete", "_wool", "_stained_glass", "_glazed_terracotta"):
        if block.endswith(material):
            darker = block[:-len(material)] + "_terracotta"
            if darker in variables.decorative_blocks:
                return darker
    return block


def chain_block_dict(chain_blocks):
    """Block lookup for chain numbers: '1'..'n' -> chain colour, '1b'..'nb' -> its darker partner."""
    blocks = {}
    for i, block in enumerate(chain_blocks, start=1):
        blocks[str(i)] = block
        blocks[f"{i}b"] = dark_block(block)
    return blocks


def valid_chain_blocks(chain_blocks):
    """The configured chain colour list, or the default list when it is empty or has no valid block."""
    blocks = [b for b in (chain_blocks or []) if b in variables.decorative_blocks]
    return blocks or list(DEFAULT_CHAIN_BLOCKS)


# --- residue modifications ---

# Optional column of a part giving each block's residue as 'chain:resid' (see ResidueModifications.apply)
RESIDUE_COLUMN = 'residue_key'


class ResidueModifications:
    """
    "Modify Residues" choices: {chain: {resid: ['hide', 'block:<name>', ...]}} as made by
    SequenceSelectorPopup. Hidden residues are left out of every part; an assigned block replaces the
    colour of every block that belongs to the residue.

    Blocks are attributed to the residue of the nearest atom, so the rule works the same for spheres,
    bond lines, ribbons and surfaces: a bond between two residues is split halfway.
    """

    def __init__(self, mods=None):
        self.hidden = set()
        self.blocks = {}
        for chain, residues in (mods or {}).items():
            for resid, options in residues.items():
                key = self.key(chain, resid)
                for option in options:
                    if option == "hide":
                        self.hidden.add(key)
                    elif option.startswith("block:"):
                        self.blocks[key] = option.split(":", 1)[1]

    @staticmethod
    def key(chain, resid):
        return f"{chain}:{int(resid)}"

    def __bool__(self):
        return bool(self.hidden or self.blocks)

    def apply(self, part, atoms):
        """
        part: blocks (X, Y, Z[, atom]); atoms: the atoms the part was built from (X, Y, Z, chain, resid).
        Blocks belong to the residue of their nearest atom, or to RESIDUE_COLUMN ('chain:resid') when the
        part has it. Returns part without hidden residues and with a 'block' column for assigned blocks.
        """
        if part is not None and RESIDUE_COLUMN in part.columns:
            owner = part[RESIDUE_COLUMN].to_numpy(dtype=object)
            part = part.drop(columns=RESIDUE_COLUMN)
            return self._apply_owner(part, owner) if self else part
        if not self or part is None or part.empty or atoms is None or atoms.empty:
            return part
        keys = (atoms['chain'].astype(str) + ":" + atoms['resid'].astype(int).astype(str)).to_numpy()
        affected = np.isin(keys, list(self.hidden | set(self.blocks)))
        if not affected.any():
            return part
        tree = cKDTree(atoms[['X', 'Y', 'Z']].to_numpy(dtype=float))
        _, nearest = tree.query(part[['X', 'Y', 'Z']].to_numpy(dtype=float))
        return self._apply_owner(part, keys[nearest])

    def _apply_owner(self, part, owner):
        part = part.copy()
        if self.blocks:
            block = pd.Series(owner).map(self.blocks).to_numpy()
            if 'block' in part.columns:
                block = np.where(pd.isna(block), part['block'].to_numpy(), block)
            part['block'] = block
        if self.hidden:
            part = part[~np.isin(owner, list(self.hidden))]
        return part


# --- block makers shared by the modes ---

def backbone_lines(df, by_chain, numbers):
    """Single-block lines along every continuous backbone segment (atom = chain number when by_chain)."""
    backbone = df[df['segment'].notna()]
    if backbone.empty:
        return EMPTY_BLOCKS.copy()
    parts = []
    groups = backbone.groupby('chain', sort=False) if by_chain else [(None, backbone)]
    for chain, chain_df in groups:
        # Connect points only within a segment: find_intermediate_points joins rows with equal 'chain'
        line = pdbm.find_intermediate_points(chain_df[['X', 'Y', 'Z']].assign(chain=chain_df['segment']))
        if line.empty:
            continue
        line = line[['X', 'Y', 'Z']].copy()
        line['atom'] = str(numbers[chain]) if chain is not None else 'backbone_atom'
        parts.append(line)
    return pd.concat(parts, ignore_index=True) if parts else EMPTY_BLOCKS.copy()


def thicken(lines, diameter):
    """Turn single-block lines into cylinders of the given diameter, keeping each block's 'atom'."""
    if lines.empty:
        return lines
    radius = float(diameter) / 2
    sphere = pdbm.add_sphere_coordinates(pdbm.rasterized_sphere(radius), pdbm.sphere_center(radius),
                                         lines[['X', 'Y', 'Z', 'atom']], mesh=False)
    return sphere.drop_duplicates(subset=['X', 'Y', 'Z'])


def linked_residue_lines(df, bonds, by_chain, numbers):
    """
    Backbone through HETATM residues that sit inside a chain, such as the GFP chromophore (CRO): the
    covalent links to the neighbouring residues plus the shortest bond path through the residue. These
    residues have no N/CA/C atoms, so without this the backbone has a gap at each of them.
    """
    if not bonds:
        return EMPTY_BLOCKS.copy()
    by_num = df.drop_duplicates('atom_num').set_index('atom_num')
    is_polymer = by_num['polymer'].to_dict()
    graph = {}
    for bond in bonds:
        a, b = int(bond['atom_num1']), int(bond['atom_num2'])
        if a in by_num.index and b in by_num.index:
            graph.setdefault(a, set()).add(b)
            graph.setdefault(b, set()).add(a)

    residue_of = (by_num['chain'].astype(str) + ":" + by_num['resid'].astype(str)).to_dict()
    entry_points = {}
    for a, neighbours in graph.items():
        if is_polymer.get(a):
            continue
        for b in neighbours:
            if is_polymer.get(b) and by_num.at[b, 'atom'] in BACKBONE_ATOMS:
                entry_points.setdefault(residue_of[a], []).append((b, a))

    lines = []
    for residue, links in entry_points.items():
        if len(links) < 2:
            continue
        (outer1, start), (outer2, end) = links[0], links[1]
        path = _shortest_path(graph, start, end, lambda n: residue_of.get(n) == residue)
        if path is None:
            continue
        chain = by_num.at[start, 'chain']
        atom = str(numbers.get(chain, 1)) if by_chain else 'backbone_atom'
        nodes = [outer1] + path + [outer2]
        for a, b in zip(nodes[:-1], nodes[1:]):
            line = pdbm.bresenham_line(*by_num.loc[a, ['X', 'Y', 'Z']].astype(int),
                                       *by_num.loc[b, ['X', 'Y', 'Z']].astype(int))
            if len(line):
                lines.append(pd.DataFrame(line, columns=['X', 'Y', 'Z']).assign(atom=atom))
    return pd.concat(lines, ignore_index=True) if lines else EMPTY_BLOCKS.copy()


def _shortest_path(graph, start, end, allowed):
    previous = {start: None}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        if node == end:
            path = []
            while node is not None:
                path.append(node)
                node = previous[node]
            return path[::-1]
        for nxt in graph.get(node, ()):
            if nxt not in previous and allowed(nxt):
                previous[nxt] = node
                queue.append(nxt)
    return None


def backbone_blocks(df, config_data, numbers, bonds=None):
    """Cylinder blocks along the backbone, including through chain-internal HETATM residues."""
    lines = backbone_lines(df, config_data["by_chain"], numbers)
    linked = linked_residue_lines(df, bonds, config_data["by_chain"], numbers)
    lines = pd.concat([lines, linked], ignore_index=True) if not linked.empty else lines
    return thicken(lines, config_data["backbone_size"])


def sidechain_blocks(df, config_data, numbers):
    """Lines along every sidechain bond from chains.txt."""
    side = df[df['polymer'] & ~df['atom'].isin(NOT_SIDECHAIN_ATOMS)]
    if side.empty:
        return EMPTY_BLOCKS.copy()
    if not config_data["by_chain"]:
        branches = pdbm.sidechain(side)
        branches['atom'] = 'sidechain_atom'
        return branches
    parts = []
    for chain, chain_df in side.groupby('chain', sort=False):
        branches = pdbm.sidechain(chain_df)
        branches['atom'] = str(numbers[chain])
        parts.append(branches)
    return pd.concat(parts, ignore_index=True).drop_duplicates()


def atom_spheres(atoms, atom_scale, mesh=False):
    """A sphere per atom, coloured by element. Mesh spheres need a diameter of at least 2 to show a shell."""
    if atoms.empty:
        return EMPTY_BLOCKS.copy()
    scale = max(atom_scale, 2) if mesh else atom_scale
    return pdbm.add_sphere_coordinates(pdbm.rasterized_sphere(scale), pdbm.sphere_center(scale),
                                       pdbm.element_atom_names(atoms), mesh=mesh)


def hetatm_atoms(df):
    return df[df['row'] == 'HETATM']


def bond_lines(df, bonds, atom_nums=None):
    """Lines for `bonds` whose atoms are both in df; with atom_nums, only bonds touching those atoms."""
    if atom_nums is not None:
        atom_nums = set(int(n) for n in atom_nums)
        bonds = [b for b in bonds if int(b['atom_num1']) in atom_nums or int(b['atom_num2']) in atom_nums]
    return pdbm.get_hetatm_bond_lines_from_df(df, bonds)


def hetatm_blocks(df, structure, config_data, mesh=False):
    """Spheres coloured by element for HETATM atoms, and lines for their bonds (including links to the polymer)."""
    het = hetatm_atoms(df)
    if het.empty:
        return EMPTY_BLOCKS.copy(), EMPTY_BLOCKS.copy()
    spheres = atom_spheres(het.reset_index(drop=True), config_data['atom_scale'], mesh=mesh)
    bonds = bond_lines(df, structure.bonds, het['atom_num'])
    return spheres, bonds


# --- builder ---

def safe_name(text):
    """Lowercase text with characters Minecraft does not allow in file names replaced by '_'."""
    return re.sub(r"[^a-z0-9_.-]", "_", str(text).lower())


class ModelBuilder:
    """
    Everything a mode needs to build one model: the prepared atoms (`df`), chain colour numbers, the
    block lookup, residue modifications and write() to save a part as <name>_<suffix>.
    """

    def __init__(self, config_data, structure, mc_dir, name=None, progress=None):
        self.config = config_data
        self.structure = structure
        self.mc_dir = mc_dir
        self.name = name or structure.name
        self._progress = progress or (lambda value: None)
        self.df = prepare_coordinates(structure, config_data['scale'])
        self.chain_blocks = valid_chain_blocks(config_data.get('chain_blocks'))
        polymer_chains = self.df.loc[self.df['polymer'], 'chain']
        self.numbers = chain_numbers(polymer_chains if len(polymer_chains) else self.df['chain'],
                                     len(self.chain_blocks))
        self.blocks = {**config_data['atoms'], **chain_block_dict(self.chain_blocks)}
        self.mods = ResidueModifications(config_data.get('residue_mods'))
        self.written = []
        self._part_names = set()

    def report(self, value):
        """Progress of the mode's own work, 0-100."""
        self._progress(value)

    def part_name(self, suffix):
        """
        <name>_<suffix> as a valid, unused Minecraft file name. Names are lowercase, so chains that differ
        only in case (mmCIF chains 'AA' and 'aa') would share a file; later ones get _2, _3, ...
        """
        base = safe_name(f"{self.name}_{suffix}")
        name, n = base, 1
        while name in self._part_names:
            n += 1
            name = f"{base}_{n}"
        self._part_names.add(name)
        return name

    def write(self, blocks, suffix, atoms=None, block_lookup=None):
        """
        Save one part. `atoms` are the atoms the blocks were built from (default: all atoms), used to
        apply residue modifications; `block_lookup` replaces the standard atom -> block lookup.
        """
        if blocks is None or blocks.empty:
            return []
        blocks = self.mods.apply(blocks, self.df if atoms is None else atoms)
        lookup = self.blocks if block_lookup is None else {**chain_block_dict(self.chain_blocks), **block_lookup}
        paths = mcf.create_nbt(blocks, self.part_name(suffix), air=False, dir=self.mc_dir, blocks=lookup)
        self.written.extend(paths)
        return paths


def mode_module(mode):
    """Backend module for a mode name as shown in the sidebar."""
    from PDB2MC import amino_acids, custom, ribbon, skeleton, space_filling
    modules = {
        "Skeleton": skeleton,
        "Custom": custom,
        "X-Ray": custom,
        "Amino Acids": amino_acids,
        "Ribbon": ribbon,
        "Space Filling": space_filling,
    }
    if mode not in modules:
        raise ValueError(f"Unknown mode: {mode}")
    return modules[mode]


def build_model(mode, config_data, progress=None):
    """
    Build the model for config_data['pdb_file'] into the world at config_data['save_path'] with the given
    mode. Returns the model name (use /function protein:build_<name>). progress gets 0-100.
    """
    report = progress or (lambda value: None)
    structure = pdbm.load_structure(config_data['pdb_file'])
    name = structure.name
    mc_dir = config_data['save_path']
    report(5)
    mcf.delete_old_files(mc_dir, name)
    report(10)
    builder = ModelBuilder(config_data, structure, mc_dir, name=name,
                           progress=lambda value: report(10 + int(value * 0.75)))
    mode_module(mode).build(builder)
    report(85)
    mcf.finish_nbts(mc_dir, config_data, name)
    mcf.create_nbt_delete(name, mc_dir)
    mcf.finish_delete_nbts(mc_dir, name)
    report(100)
    return name
