from Bio.PDB import PDBParser, MMCIFParser
from Bio.PDB.Polypeptide import is_aa
import pandas as pd
import re

# Helper function for nucleic acid detection
NUCLEOTIDE_CODES = {'A', 'C', 'G', 'T', 'U', 'DA', 'DC', 'DG', 'DT', 'DU', 'ADE', 'CYT', 'GUA', 'THY', 'URA'}

def is_nucleotide_residue(residue):
    return residue.get_resname().strip().upper() in NUCLEOTIDE_CODES

def three_to_one(resname):
    # Standard amino acid and nucleotide conversion
    table = {
        'ALA': 'A', 'ARG': 'R', 'ASN': 'N', 'ASP': 'D', 'CYS': 'C',
        'GLN': 'Q', 'GLU': 'E', 'GLY': 'G', 'HIS': 'H', 'ILE': 'I',
        'LEU': 'L', 'LYS': 'K', 'MET': 'M', 'PHE': 'F', 'PRO': 'P',
        'SER': 'S', 'THR': 'T', 'TRP': 'W', 'TYR': 'Y', 'VAL': 'V',
        # DNA/RNA nucleotides
        'A': 'A', 'C': 'C', 'G': 'G', 'T': 'T', 'U': 'U',
        'DA': 'A', 'DC': 'C', 'DG': 'G', 'DT': 'T', 'DU': 'U',
        # Common alternate codes
        'ASX': 'B', 'GLX': 'Z', 'UNK': 'X'
    }
    return table.get(str(resname).upper(), '?')

class StructureData:
    def __init__(self):
        self.atoms = []
        self.metadata = {}
        self.structural_info = pd.DataFrame(
            columns=['chain', 'residue1', 'resid1', 'residue2', 'resid2', 'structure']
        )
        # sequences: maps chain -> list of tuples (true_resid, one_letter_code)
        # - true_resid: the original residue id from the file (auth seq id); used for downstream references
        # - one_letter_code: single-letter amino acid / nucleotide code
        self.sequences = {}  # chain_id: list of (true_resid, single_letter_code)
        self.bonds = []      # List of dicts: {'atom_num1': int, 'atom_num2': int}
        self.chain_identity = {}  # chain_id: molecule name

    @classmethod
    def from_pdb(cls, file_path):
        parser = PDBParser(QUIET=True)
        # Try to get PDB id from HEADER line
        pdb_id = None
        with open(file_path) as f:
            for line in f:
                if line.startswith("HEADER") and len(line) >= 66:
                    pdb_id = line[62:66].strip()
                    break
        structure = parser.get_structure(pdb_id if pdb_id else "unknown", file_path)
        instance = cls()
        atom_num_map = {}  # Map (chain, resid, atom name, is_hetatm) -> atom_num
        # Parse header for metadata and secondary structure
        with open(file_path) as f:
            for line in f:
                if line.startswith("HEADER"):
                    instance.metadata['header'] = line[10:].strip()
                elif line.startswith("TITLE"):
                    instance.metadata.setdefault('title', '')
                    instance.metadata['title'] += line[10:].strip() + ' '
                elif line.startswith("AUTHOR"):
                    instance.metadata.setdefault('author', '')
                    instance.metadata['author'] += line[10:].strip() + ' '
                elif line.startswith("REMARK   2 RESOLUTION."):
                    instance.metadata['resolution'] = line[22:].strip()
                elif line.startswith("EXPDTA"):
                    instance.metadata['experimental_method'] = line[10:].strip()
                elif line.startswith("HELIX"):
                    data = {
                        'chain': line[19].strip(),
                        'residue1': line[15:18].strip(),
                        'resid1': line[21:25].strip(),
                        'residue2': line[27:30].strip(),
                        'resid2': line[33:37].strip(),
                        'structure': "helix"
                    }
                    instance.structural_info = pd.concat(
                        [instance.structural_info, pd.DataFrame(data, index=[0])],
                        ignore_index=True
                    )
                elif line.startswith("SHEET"):
                    data = {
                        'chain': line[21].strip(),
                        'residue1': line[17:20].strip(),
                        'resid1': line[22:26].strip(),
                        'residue2': line[28:31].strip(),
                        'resid2': line[33:37].strip(),
                        'structure': "sheet"
                    }
                    instance.structural_info = pd.concat(
                        [instance.structural_info, pd.DataFrame(data, index=[0])],
                        ignore_index=True
                    )
                elif line.startswith("END"):
                    break
        # Clean up structural_info
        if not instance.structural_info.empty:
            instance.structural_info = instance.structural_info[
                instance.structural_info['chain'].str.strip().astype(bool)
            ]
            instance.structural_info[['resid1', 'resid2']] = instance.structural_info[['resid1', 'resid2']].astype(int)
        # Parse atoms and build atom_num_map
        with open(file_path) as f:
            for line in f:
                if line.startswith(('ATOM', 'HETATM')):
                    atom_num = int(line[6:11].strip())
                    atom_name = line[12:16].strip()
                    residue = line[17:20].strip()
                    chain = line[21].strip()
                    resid = int(line[22:26].strip())
                    hetatm = line.startswith('HETATM')
                    element = line[76:78].strip() if len(line) >= 78 else ''
                    # Ignore hydrogens
                    if element.upper() == 'H' or atom_name.upper().startswith('H'):
                        continue
                    atom_dict = {
                        'atom_num': atom_num,
                        'name': atom_name,
                        'atom': atom_name,
                        'residue': residue,
                        'chain': chain,
                        'res_id': resid,
                        'resid': resid,
                        'x': float(line[30:38].strip()),
                        'y': float(line[38:46].strip()),
                        'z': float(line[46:54].strip()),
                        'element': element,
                        'hetatm': hetatm
                    }
                    instance.atoms.append(atom_dict)
                    atom_num_map[(chain, resid, atom_name, hetatm)] = atom_num
        # Parse CONECT lines for bonds (HETATM only)
        with open(file_path) as f:
            for line in f:
                if line.startswith("CONECT"):
                    fields = line.split()
                    if len(fields) < 3:
                        continue
                    src = int(fields[1])
                    for tgt_str in fields[2:]:
                        try:
                            tgt = int(tgt_str)
                        except ValueError:
                            continue
                        # Only add bonds if both atoms are HETATM
                        src_atom = next((a for a in instance.atoms if a['atom_num'] == src), None)
                        tgt_atom = next((a for a in instance.atoms if a['atom_num'] == tgt), None)
                        if src_atom and tgt_atom and (src_atom['hetatm'] or tgt_atom['hetatm']):
                            if src != tgt:
                                instance.bonds.append({'atom_num1': src, 'atom_num2': tgt})
        # Build sequence per chain
        chain_residues = {}
        for atom in instance.atoms:
            chain = atom['chain']
            resid = atom['resid']            # true residue id from PDB file
            resname = atom['residue']
            # Only add first atom for each residue
            if chain not in chain_residues:
                chain_residues[chain] = []
            if not chain_residues[chain] or chain_residues[chain][-1][0] != resid:
                # Only add if amino acid or nucleotide
                code = three_to_one(resname)
                if code != '?':
                    # store as (true_resid, code)
                    chain_residues[chain].append((resid, code))

        # Use the simple (true_resid, code) format for sequences
        instance.sequences = {c: seq for c, seq in chain_residues.items()}
        instance.metadata['id'] = pdb_id if pdb_id else structure.id
        instance.metadata['source_file'] = file_path

        # --- Improved CMPND parsing for chain identity ---
        cmpnd_lines = []
        with open(file_path) as f:
            for line in f:
                if line.startswith("COMPND"):
                    cmpnd_lines.append(line[10:].strip())

        chain_identity = {}
        if cmpnd_lines:
            full = " ".join(cmpnd_lines)
            # split into fields by semicolon; keep order
            tokens = [t.strip() for t in full.split(";") if t.strip()]

            current_molecule = None
            for token in tokens:
                # MOLECULE: <name>
                m = re.match(r'^\s*MOLECULE:\s*(.+)$', token, flags=re.I)
                if m:
                    current_molecule = m.group(1).strip()
                    # remove any trailing commas or periods
                    current_molecule = current_molecule.rstrip(".,")
                    continue

                # CHAIN: A, B, C
                c = re.match(r'^\s*CHAIN:\s*(.+)$', token, flags=re.I)
                if c and current_molecule:
                    chains_raw = c.group(1).strip()
                    # split on commas, strip whitespace and ignore empty parts
                    chains = [ch.strip() for ch in chains_raw.split(",") if ch.strip()]
                    for ch in chains:
                        chain_identity[ch] = current_molecule
                    # consume the molecule so only the first CHAIN is associated with it
                    current_molecule = None

        instance.chain_identity = chain_identity
        # ------------------------------------------------
        return instance

    def save_to_file(self, base_path):
        # Save metadata
        with open(f"{base_path}_metadata.txt", "w") as f:
            for key, value in self.metadata.items():
                f.write(f"{key}: {value}\n")
        # Save structural_info DataFrame
        self.structural_info.to_csv(f"{base_path}_structural_info.csv", index=False)
        # Save atoms list
        import pandas as pd
        pd.DataFrame(self.atoms).to_csv(f"{base_path}_atoms.csv", index=False)

    @classmethod
    def from_mmcif(cls, file_path):
        parser = MMCIFParser(QUIET=True)
        structure = parser.get_structure("unknown", file_path)
        instance = cls()
        mmcif_dict = parser._mmcif_dict
        # Try to get PDB id from _entry.id
        pdb_id = None
        if '_entry.id' in mmcif_dict:
            pdb_id = mmcif_dict['_entry.id'][0]
        # Metadata
        instance.metadata['id'] = pdb_id if pdb_id else structure.id
        instance.metadata['header'] = mmcif_dict.get('_struct.title', [''])[0]
        instance.metadata['title'] = mmcif_dict.get('_struct.title', [''])[0]
        instance.metadata['author'] = ', '.join(mmcif_dict.get('_audit_author.name', []))
        instance.metadata['resolution'] = mmcif_dict.get('_refine.ls_d_res_high', [''])[0]
        instance.metadata['experimental_method'] = mmcif_dict.get('_exptl.method', [''])[0]

        # Secondary structure: helices and sheets
        # Helices
        helix_fields = [
            '_struct_conf.conf_type_id',
            '_struct_conf.beg_auth_asym_id',
            '_struct_conf.beg_auth_comp_id',
            '_struct_conf.beg_auth_seq_id',
            '_struct_conf.end_auth_asym_id',
            '_struct_conf.end_auth_comp_id',
            '_struct_conf.end_auth_seq_id'
        ]
        if all(field in mmcif_dict for field in helix_fields):
            for i, conf_type in enumerate(mmcif_dict['_struct_conf.conf_type_id']):
                if 'HELX' in conf_type:
                    data = {
                        'chain': mmcif_dict['_struct_conf.beg_auth_asym_id'][i],
                        'residue1': mmcif_dict['_struct_conf.beg_auth_comp_id'][i],
                        'resid1': mmcif_dict['_struct_conf.beg_auth_seq_id'][i],
                        'residue2': mmcif_dict['_struct_conf.end_auth_comp_id'][i],
                        'resid2': mmcif_dict['_struct_conf.end_auth_seq_id'][i],
                        'structure': 'helix'
                    }
                    instance.structural_info = pd.concat(
                        [instance.structural_info, pd.DataFrame(data, index=[0])],
                        ignore_index=True
                    )
        # Sheets
        sheet_fields = [
            '_struct_sheet_range.sheet_id',
            '_struct_sheet_range.beg_auth_asym_id',
            '_struct_sheet_range.beg_auth_comp_id',
            '_struct_sheet_range.beg_auth_seq_id',
            '_struct_sheet_range.end_auth_asym_id',
            '_struct_sheet_range.end_auth_comp_id',
            '_struct_sheet_range.end_auth_seq_id'
        ]
        if all(field in mmcif_dict for field in sheet_fields):
            for i in range(len(mmcif_dict['_struct_sheet_range.sheet_id'])):
                data = {
                    'chain': mmcif_dict['_struct_sheet_range.beg_auth_asym_id'][i],
                    'residue1': mmcif_dict['_struct_sheet_range.beg_auth_comp_id'][i],
                    'resid1': mmcif_dict['_struct_sheet_range.beg_auth_seq_id'][i],
                    'residue2': mmcif_dict['_struct_sheet_range.end_auth_comp_id'][i],
                    'resid2': mmcif_dict['_struct_sheet_range.end_auth_seq_id'][i],
                    'structure': 'sheet'
                }
                instance.structural_info = pd.concat(
                    [instance.structural_info, pd.DataFrame(data, index=[0])],
                    ignore_index=True
                )

        # Clean up structural_info
        if not instance.structural_info.empty:
            instance.structural_info = instance.structural_info[
                instance.structural_info['chain'].str.strip().astype(bool)
            ]
            instance.structural_info[['resid1', 'resid2']] = instance.structural_info[['resid1', 'resid2']].astype(int)

        # Parse atoms
        atom_site = mmcif_dict
        atom_ids = atom_site.get('_atom_site.id', [])
        atom_names = atom_site.get('_atom_site.label_atom_id', [])
        res_names = atom_site.get('_atom_site.label_comp_id', [])
        chains = atom_site.get('_atom_site.auth_asym_id', [])
        res_ids = atom_site.get('_atom_site.auth_seq_id', [])
        label_asym_ids = atom_site.get('_atom_site.label_asym_id', [])
        x_coords = atom_site.get('_atom_site.Cartn_x', [])
        y_coords = atom_site.get('_atom_site.Cartn_y', [])
        z_coords = atom_site.get('_atom_site.Cartn_z', [])
        elements = atom_site.get('_atom_site.type_symbol', [])
        groups = atom_site.get('_atom_site.group_PDB', [])
        # Build atom list and atom_num_map
        for i in range(len(atom_ids)):
            group = groups[i].strip()
            try:
                atom_num = int(atom_ids[i])
            except Exception:
                continue
            atom_name = atom_names[i].strip()
            residue = res_names[i].strip()
            chain = chains[i].strip()
            resid = int(res_ids[i])
            label_asym_id = label_asym_ids[i].strip() if label_asym_ids else ""
            element = elements[i].strip()
            hetatm = (group == "HETATM")
            # Ignore hydrogens
            if element.upper() == 'H' or atom_name.upper().startswith('H'):
                continue
            atom_dict = {
                'atom_num': atom_num,
                'name': atom_name,
                'atom': atom_name,
                'residue': residue,
                'chain': chain,
                'res_id': resid,
                'resid': resid,
                'label_asym_id': label_asym_id,
                'x': float(x_coords[i]),
                'y': float(y_coords[i]),
                'z': float(z_coords[i]),
                'element': element,
                'hetatm': hetatm
            }
            instance.atoms.append(atom_dict)
        # Build bonds for HETATMs using _chem_comp_bond
        bonds = []
        if '_chem_comp_bond.comp_id' in mmcif_dict:
            comp_ids = mmcif_dict['_chem_comp_bond.comp_id']
            atom_id_1s = mmcif_dict['_chem_comp_bond.atom_id_1']
            atom_id_2s = mmcif_dict['_chem_comp_bond.atom_id_2']
            # Group all HETATM atoms by (residue, label_asym_id)
            hetatm_atoms = [a for a in instance.atoms if a['hetatm']]
            # Group by (residue, chain, label_asym_id, res_id) for uniqueness
            hetatm_groups = {}
            for a in hetatm_atoms:
                key = (a['residue'], a['chain'], a.get('label_asym_id', ''), a['resid'])
                hetatm_groups.setdefault(key, []).append(a)
            # For each bond template, apply to each instance of the chemical
            for comp_id, atom1, atom2 in zip(comp_ids, atom_id_1s, atom_id_2s):
                # Ignore hydrogens
                if atom1.upper().startswith('H') or atom2.upper().startswith('H'):
                    continue
                for key, atoms in hetatm_groups.items():
                    residue, chain, label_asym_id, resid = key
                    if residue != comp_id:
                        continue
                    atoms_1 = [a for a in atoms if a['atom'] == atom1]
                    atoms_2 = [a for a in atoms if a['atom'] == atom2]
                    for a1 in atoms_1:
                        for a2 in atoms_2:
                            if a1['atom_num'] != a2['atom_num']:
                                bonds.append({'atom_num1': a1['atom_num'], 'atom_num2': a2['atom_num']})
        instance.bonds = bonds
        # Build sequence per chain
        chain_residues = {}
        for atom in instance.atoms:
            chain = atom['chain']
            resid = atom['resid']  # true residue id from mmCIF auth_seq_id
            resname = atom['residue']
            if chain not in chain_residues:
                chain_residues[chain] = []
            if not chain_residues[chain] or chain_residues[chain][-1][0] != resid:
                code = three_to_one(resname)
                if code != '?':
                    # store as (true_resid, code)
                    chain_residues[chain].append((resid, code))

        # Use the simple (true_resid, code) format for sequences
        instance.sequences = {c: seq for c, seq in chain_residues.items()}
        instance.metadata['source_file'] = file_path

        # Parse entity names and map to chains
        chain_identity = {}
        # Get entity names
        entity_names = mmcif_dict.get('_entity_name_com.name', [])
        entity_ids = mmcif_dict.get('_entity_poly.entity_id', [])
        strand_ids = mmcif_dict.get('_entity_poly.pdbx_strand_id', [])
        # Map entity_id to name
        entity_id_to_name = {}
        for i, eid in enumerate(entity_ids):
            name = entity_names[i] if i < len(entity_names) else ""
            entity_id_to_name[eid] = name
        # Map chain to name via entity_id
        for i, eid in enumerate(entity_ids):
            chains = strand_ids[i].replace(" ", "").split(",")
            name = entity_id_to_name.get(eid, "")
            for c in chains:
                chain_identity[c] = name
        instance.chain_identity = chain_identity
        return instance
