"""Ribbon mode: smoothed backbone with flat helix/sheet ribbons (or helix rods), nucleic acid ladders."""
import pandas as pd

from PDB2MC import pdb_manipulation as pdbm
from PDB2MC.build import ModelBuilder, hetatm_blocks, part_work

AMINO_ACIDS = ["ALA", "ARG", "ASN", "ASP", "CYS", "GLN", "GLU", "GLY", "HIS", "ILE", "LEU", "LYS", "MET",
               "PHE", "PRO", "SER", "THR", "TRP", "TYR", "VAL", "MSE"]
NUCLEOTIDES = ["A", "C", "G", "U", "DA", "DC", "DG", "DT", "DI"]
RIBOSE_ATOMS = ["C1'", "C2'", "C3'", "C4'", "O4'"]
BASE_ATOMS = ["N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9"]
RIBBON_BACKBONE_ATOMS = ['C', 'N', 'CA', "C4'", "C3'"]
SMOOTHNESS = 5000
# Relative time per atom of a chain, for the progress bar: DNA and RNA ladders are far slower than ribbons
PROTEIN_WORK = 1
NUCLEIC_WORK = 7
# Relative time per expected block of other molecules
HETATM_WORK = 0.02


def protein_ribbon(chain_df, vectors_df, bar_helix, scale, progress=None):
    """Ribbon blocks for one protein chain: flat helices/sheets, plus helix rods with bar_helix."""
    report = progress or (lambda fraction: None)
    intermediate = pdbm.find_intermediate_points(chain_df, keep_columns=True, atoms=["CA", "C", "N"])
    report(0.1)
    ribbon = pdbm.interpolate_dataframe(intermediate, smoothness=SMOOTHNESS)
    report(0.4)
    structure = chain_df['structure']
    if structure.str.contains('helix').any() or structure.str.contains('sheet').any():
        try:
            ribbon = pdbm.flank_coordinates(ribbon, vectors_df, bar=bar_helix)
        except Exception:
            # flanking needs C=O vectors for every residue; draw the plain trace when they are missing
            pass
    report(0.7)
    if bar_helix and structure.str.contains('helix').any():
        trace = pdbm.find_intermediate_points(chain_backbone(chain_df), fill_columns=True, keep_columns=True)
        trace = pdbm.interpolate_dataframe(trace, SMOOTHNESS)
        # process_bars draws a rod across each gap that removing the helices leaves in the trace
        coil = trace[~trace['structure'].str.contains('helix')].reset_index(drop=True)
        bars = pdbm.process_bars(coil, size=scale * 2)
        ribbon = pd.concat([ribbon, bars[['X', 'Y', 'Z']]], ignore_index=True)
    report(1.0)
    return ribbon[['X', 'Y', 'Z']]


def chain_backbone(chain_df):
    return chain_df[chain_df['atom'].isin(RIBBON_BACKBONE_ATOMS)]


def protein_backbone(chain_df, bar_helix, progress=None):
    """Smoothed backbone trace; with helix rods / ribbons the trace is only drawn outside them."""
    report = progress or (lambda fraction: None)
    trace = pdbm.find_intermediate_points(chain_backbone(chain_df), fill_columns=True, keep_columns=True)
    report(0.3)
    trace = pdbm.interpolate_dataframe(trace, SMOOTHNESS)
    if bar_helix:
        trace = trace[~trace['structure'].str.contains('helix') & ~trace['structure'].str.contains('sheet')]
    return trace[['X', 'Y', 'Z']]


def nucleic_backbone(chain_df, dna_vectors, progress=None):
    trace = pdbm.find_intermediate_points(chain_backbone(chain_df), keep_columns=True)
    trace = pdbm.interpolate_dataframe(trace, SMOOTHNESS)
    return pdbm.flank_DNA(trace, dna_vectors, progress=progress)[['X', 'Y', 'Z']]


def chain_work(chain_df):
    """Expected work of a chain's ribbon and backbone."""
    residues = chain_df["residue"]
    if residues.isin(AMINO_ACIDS).any():
        return len(chain_df) * PROTEIN_WORK
    if residues.isin(NUCLEOTIDES).any():
        return len(chain_df) * NUCLEIC_WORK
    return 0


def build(builder):
    """Write <name>_<chain>_ribbon and <name>_<chain>_backbone per chain, plus _hetatm and _hetatm_bonds."""
    config = builder.config
    by_chain = config["by_chain"]
    bar_helix = config.get('bar_style', False)
    atoms = builder.df
    df = atoms[atoms['polymer']].drop(columns=['polymer', 'segment'])
    df = pdbm.add_structure_from_structured_data(df, builder.structure)

    vectors = pdbm.CO_vectors(df, width=1)
    dna_vectors = pdbm.DNA_vectors(df, width=1)
    chains = pdbm.enumerate_chains(df)
    het_work = part_work(atoms, config)
    builder.report(4)
    builder.plan({**{chain: chain_work(pdbm.get_chain(df, chain)) for chain in chains},
                  "hetatm": het_work["hetatm"] * HETATM_WORK, "hetatm_bonds": het_work["hetatm_bonds"] * HETATM_WORK})

    for chain in chains:
        chain_df = pdbm.get_chain(df, chain)
        colour = str(builder.numbers.get(chain, 1))
        residues = chain_df["residue"]
        within = builder.step(chain, f"Drawing chain {chain}...", compute=0.95)
        if residues.isin(AMINO_ACIDS).any():
            ribbon = protein_ribbon(chain_df, pdbm.get_chain(vectors, chain), bar_helix, config['scale'],
                                    progress=lambda fraction: within(0.6 * fraction))
            backbone = None
            if config["backbone"]:
                backbone = protein_backbone(chain_df, bar_helix, progress=lambda fraction: within(0.6 + 0.4 * fraction))
        elif residues.isin(NUCLEOTIDES).any():
            ribbon = pdbm.sidechain(chain_df[chain_df["atom"].isin(RIBOSE_ATOMS + BASE_ATOMS)])[['X', 'Y', 'Z']]
            backbone = nucleic_backbone(chain_df, dna_vectors, progress=within) if config["backbone"] else None
        else:
            continue
        within(1.0)

        ribbon = ribbon.astype(float).round().astype(int)
        ribbon['atom'] = colour if by_chain else "ribbon_atom"
        builder.write(ribbon, f"{chain}_ribbon", atoms=chain_df)
        if backbone is not None and not backbone.empty:
            backbone = backbone.astype(float).round().astype(int)
            backbone['atom'] = colour if by_chain else "backbone_atom"
            builder.write(backbone, f"{chain}_backbone", atoms=chain_df)

    if config["show_hetatm"]:
        builder.step("hetatm", "Placing the other molecules...")
        spheres, bonds = hetatm_blocks(atoms, builder.structure, config)
        builder.write(spheres, "hetatm")
        builder.step("hetatm_bonds")
        builder.write(bonds, "hetatm_bonds")
    builder.report(100)


def run_mode(config_data, pdb_name, structure, mc_dir, progress=None):
    build(ModelBuilder(config_data, structure, mc_dir, name=pdb_name, progress=progress))
