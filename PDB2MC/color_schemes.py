"""
Colour schemes: what "Color ... by" colours the backbone, sidechains, ribbons or surface by. Edit the blocks and
levels here; no other file needs to change.

    Chain           each chain its own colour, from the chain colour list
    Molecule        every copy of the same molecule (protein, DNA, ...) the same colour, from the chain colour list
    Hydrophobicity  each residue by how much it avoids water (Kyte-Doolittle scale), blue (likes water) to orange
    Charge          each residue by its charge at neutral pH: positive blue, negative red; DNA and RNA are negative
    Confidence      each residue by how sure the structure is about its position: blue (sure) to orange (unsure).
                    For experimental structures this is the B-factor, compared within the model; for AlphaFold
                    predictions it is pLDDT, with AlphaFold's own thresholds.

The residue schemes colour only what the chain colours would have coloured, so element colours stay as they are.
"""
import math

import numpy as np
import pandas as pd

SCHEMES = ["Chain", "Molecule", "Hydrophobicity", "Charge", "Confidence"]
# Schemes that colour each residue rather than each chain
RESIDUE_SCHEMES = ("Hydrophobicity", "Charge", "Confidence")

# Residues a scheme has nothing to say about (unknown residues, or no B-factors in the file)
OTHER = "scheme_other"
OTHER_BLOCK = "light_gray_concrete"

# Kyte & Doolittle (1982) hydropathy: positive avoids water
HYDROPATHY = {
    "ILE": 4.5, "VAL": 4.2, "LEU": 3.8, "PHE": 2.8, "CYS": 2.5, "MET": 1.9, "ALA": 1.8, "GLY": -0.4,
    "THR": -0.7, "SER": -0.8, "TRP": -0.9, "TYR": -1.3, "PRO": -1.6, "HIS": -3.2, "GLU": -3.5, "GLN": -3.5,
    "ASP": -3.5, "ASN": -3.5, "LYS": -3.9, "ARG": -4.5,
}
# (lowest hydropathy of the level, block), from most water-loving to most water-avoiding
HYDROPHOBICITY_LEVELS = [
    (-math.inf, "blue_concrete"),        # Arg, Lys, Asn, Asp, Gln, Glu, His
    (-3.0, "light_blue_concrete"),       # Pro, Tyr
    (-1.0, "white_concrete"),            # Trp, Ser, Thr, Gly
    (1.0, "yellow_concrete"),            # Ala, Met
    (2.5, "orange_concrete"),            # Cys, Phe, Leu, Val, Ile
]

POSITIVE = {"LYS", "ARG"}
NEGATIVE = {"ASP", "GLU", "A", "C", "G", "U", "T", "DA", "DC", "DG", "DT", "DU"}
CHARGE_BLOCKS = {"positive": "blue_concrete", "negative": "red_concrete", "neutral": "white_concrete"}

# Confidence levels, most confident first
CONFIDENCE_BLOCKS = ["blue_concrete", "light_blue_concrete", "yellow_concrete", "orange_concrete"]
# AlphaFold's pLDDT bands: very high > 90, confident > 70, low > 50, very low
PLDDT_LEVELS = [90, 70, 50]


def _labels():
    labels = {OTHER: OTHER_BLOCK}
    labels.update({f"hydrophobicity_{i}": block for i, (_, block) in enumerate(HYDROPHOBICITY_LEVELS, start=1)})
    labels.update({f"charge_{kind}": block for kind, block in CHARGE_BLOCKS.items()})
    labels.update({f"confidence_{i}": block for i, block in enumerate(CONFIDENCE_BLOCKS, start=1)})
    return labels


# Block of every label the residue schemes give
BLOCKS = _labels()


def residue_key(chain, resid):
    """The same 'chain:resid' key as residue modifications use."""
    return f"{chain}:{int(resid)}"


def molecule_groups(chains, structure):
    """
    {chain: molecule} for "Molecule": the molecule name from the file, else the chain's sequence (so identical
    copies match even without names), else the chain itself.
    """
    names = getattr(structure, 'chain_identity', {}) or {}
    sequences = getattr(structure, 'sequences', {}) or {}
    groups = {}
    for chain in pd.unique(pd.Series(list(chains), dtype=object)):
        name = str(names.get(chain) or "").strip()
        sequence = "".join(code for _, code in sequences.get(chain, []))
        groups[chain] = ("name", name.upper()) if name else ("sequence", sequence) if sequence else ("chain", chain)
    return groups


def hydrophobicity_label(residue):
    value = HYDROPATHY.get(str(residue).upper())
    if value is None:
        return OTHER
    level = sum(value >= low for low, _ in HYDROPHOBICITY_LEVELS)
    return f"hydrophobicity_{level}"


def charge_label(residue):
    residue = str(residue).upper()
    if residue in POSITIVE:
        return "charge_positive"
    if residue in NEGATIVE:
        return "charge_negative"
    return "charge_neutral" if residue in HYDROPATHY else OTHER


def confidence_labels(values, predicted):
    """Confidence label of each residue from its mean B-factor (or pLDDT when predicted), as a Series."""
    valid = values.dropna()
    labels = pd.Series(OTHER, index=values.index, dtype=object)
    if predicted:
        level = 1 + sum((valid <= threshold).astype(int) for threshold in PLDDT_LEVELS)
    else:
        if len(valid) < 2 or valid.nunique() < 2:
            return labels      # no B-factors, or all the same: nothing to compare
        # Quarters of the model, lowest B-factor (most certain) first
        rank = valid.rank(method='first') - 1
        level = 1 + np.floor(len(CONFIDENCE_BLOCKS) * rank / len(valid)).astype(int)
    labels[valid.index] = "confidence_" + level.astype(int).astype(str)
    return labels


def residue_labels(df, scheme, predicted=False):
    """{'chain:resid': label} for the residues of df (atoms with chain, resid, residue, bfactor) under a scheme."""
    if df.empty:
        return {}
    keys = df['chain'].astype(str) + ":" + df['resid'].astype(int).astype(str)
    residues = df.groupby(keys.to_numpy(), sort=False)
    if scheme == "Hydrophobicity":
        return {key: hydrophobicity_label(name) for key, name in residues['residue'].first().items()}
    if scheme == "Charge":
        return {key: charge_label(name) for key, name in residues['residue'].first().items()}
    if scheme == "Confidence":
        values = pd.to_numeric(df['bfactor'], errors='coerce') if 'bfactor' in df else pd.Series(np.nan, index=df.index)
        means = values.groupby(keys.to_numpy(), sort=False).mean()
        return confidence_labels(means, predicted).to_dict()
    raise ValueError(f"Not a residue colour scheme: {scheme}")
