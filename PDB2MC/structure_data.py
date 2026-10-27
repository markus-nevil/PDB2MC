import os
import re
import numpy as np
import pandas as pd

# Helper function for nucleic acid detection
NUCLEOTIDE_CODES = {'A', 'C', 'G', 'T', 'U', 'DA', 'DC', 'DG', 'DT', 'DU', 'ADE', 'CYT', 'GUA', 'THY', 'URA'}

# Elements treated as hydrogen (D = deuterium) and dropped while parsing
HYDROGEN_ELEMENTS = {'H', 'D'}

STRUCTURAL_INFO_COLUMNS = ['chain', 'residue1', 'resid1', 'residue2', 'resid2', 'structure']

WATER_RESIDUES = {'HOH', 'WAT', 'DOD', 'H2O'}

# Covalent radii (Angstrom) used to infer HETATM bonds that the file does not list
COVALENT_RADII = {
    'C': 0.76, 'N': 0.71, 'O': 0.66, 'S': 1.05, 'P': 1.07, 'SE': 1.20, 'F': 0.57, 'CL': 1.02,
    'BR': 1.20, 'I': 1.39, 'B': 0.84, 'SI': 1.11, 'FE': 1.32, 'ZN': 1.22, 'MG': 1.41, 'CA': 1.76,
    'MN': 1.39, 'CO': 1.26, 'NI': 1.24, 'CU': 1.32, 'MO': 1.54, 'W': 1.62, 'V': 1.53, 'NA': 1.66,
    'K': 2.03, 'HG': 1.32, 'PT': 1.36, 'AU': 1.36, 'AS': 1.19, 'CD': 1.44,
}
DEFAULT_COVALENT_RADIUS = 1.0
BOND_TOLERANCE = 0.45


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


def minecraft_name(text):
    """
    Turn a file name / id into a valid Minecraft resource name: lowercase a-z, 0-9, '_', '-', '.'.
    Used as the prefix of every generated structure and function (e.g. build_<name>).
    """
    name = re.sub(r'[^a-z0-9_.-]+', '_', str(text).lower()).strip('_.-')
    return name or 'model'


def _infer_pdb_element(line, hetatm):
    """Element for PDB lines that leave columns 77-78 blank (older files)."""
    raw = line[12:14]
    if raw[0] == ' ' or raw[0].isdigit():
        return raw[1].strip().upper()
    if hetatm:
        # HETATM names such as 'FE', 'MG', 'CL' start in column 13 and are element symbols
        return ''.join(c for c in raw if c.isalpha()).upper()
    # ATOM names that start in column 13 are 4-character names (mostly hydrogens, e.g. 'HG21')
    return raw[0].upper()


class _AltlocFilter:
    """
    Keep a single conformer per residue: atoms without an altloc, plus the first altloc
    seen for that residue. Without this every alternate conformation is drawn, giving
    doubled atoms and zig-zag backbones.
    """
    def __init__(self):
        self._chosen = {}

    def keep(self, residue_key, altloc):
        if altloc in ('', ' ', '.', '?'):
            return True
        chosen = self._chosen.setdefault(residue_key, altloc)
        return altloc == chosen


def _clean_structural_info(rows):
    info = pd.DataFrame(rows, columns=STRUCTURAL_INFO_COLUMNS)
    if info.empty:
        return info
    info = info[info['chain'].astype(str).str.strip().astype(bool)]
    for col in ('resid1', 'resid2'):
        info[col] = pd.to_numeric(info[col], errors='coerce')
    info = info.dropna(subset=['resid1', 'resid2'])
    info[['resid1', 'resid2']] = info[['resid1', 'resid2']].astype(int)
    return info.reset_index(drop=True)


def infer_bonds(atoms):
    """
    Bonds between the atoms of one residue, from their distances: two atoms are bonded when they are
    closer than the sum of their covalent radii plus BOND_TOLERANCE. Returns (atom_num1, atom_num2) pairs.
    """
    if len(atoms) < 2:
        return []
    coords = np.array([(a['x'], a['y'], a['z']) for a in atoms], dtype=float)
    radii = np.array([COVALENT_RADII.get(a['element'], DEFAULT_COVALENT_RADIUS) for a in atoms])
    dist = np.linalg.norm(coords[:, None, :] - coords[None, :, :], axis=2)
    limit = radii[:, None] + radii[None, :] + BOND_TOLERANCE
    i, j = np.nonzero(np.triu((dist <= limit) & (dist > 0.4), k=1))
    return [(atoms[a]['atom_num'], atoms[b]['atom_num']) for a, b in zip(i, j)]


def complete_hetatm_bonds(atoms, bonds, links=()):
    """
    Final HETATM bond list of a structure: `bonds` as given (CONECT / chem_comp_bond), plus
    `links` (LINK / struct_conn: pairs of (chain, resid, atom name) keys), plus bonds inferred from
    distances for every HETATM residue that has no bond inside it yet. Many files (e.g. the GFP
    chromophore) have no CONECT records at all, which left those molecules as loose atoms with no
    connection to the backbone. Returns a list of {'atom_num1', 'atom_num2'} dicts without duplicates.
    """
    seen = set()
    result = []

    def add(num1, num2):
        pair = (min(num1, num2), max(num1, num2))
        if num1 != num2 and pair not in seen:
            seen.add(pair)
            result.append({'atom_num1': num1, 'atom_num2': num2})

    for bond in bonds:
        add(bond['atom_num1'], bond['atom_num2'])

    by_key = {}
    for atom in atoms:
        by_key.setdefault((atom['chain'], atom['resid'], atom['atom']), atom)
    for key1, key2 in links:
        a1, a2 = by_key.get(key1), by_key.get(key2)
        if a1 is not None and a2 is not None and (a1['hetatm'] or a2['hetatm']):
            add(a1['atom_num'], a2['atom_num'])

    residues = {}
    for atom in atoms:
        if atom['hetatm'] and atom['residue'] not in WATER_RESIDUES:
            residues.setdefault((atom['chain'], atom['resid'], atom['residue']), []).append(atom)
    residue_of = {atom['atom_num']: key for key, members in residues.items() for atom in members}
    bonded_inside = set()
    for bond in result:
        key = residue_of.get(bond['atom_num1'])
        if key is not None and key == residue_of.get(bond['atom_num2']):
            bonded_inside.add(key)
    for key, members in residues.items():
        if key not in bonded_inside:
            for num1, num2 in infer_bonds(members):
                add(num1, num2)
    return result


class StructureData:
    def __init__(self):
        self.atoms = []
        self.metadata = {}
        self.structural_info = pd.DataFrame(columns=STRUCTURAL_INFO_COLUMNS)
        # sequences: maps chain -> list of tuples (true_resid, one_letter_code)
        # - true_resid: the original residue id from the file (auth seq id); used for downstream references
        # - one_letter_code: single-letter amino acid / nucleotide code
        self.sequences = {}  # chain_id: list of (true_resid, single_letter_code)
        self.bonds = []      # List of dicts: {'atom_num1': int, 'atom_num2': int}
        self.chain_identity = {}  # chain_id: molecule name

    @property
    def name(self):
        """Minecraft-safe model name used for all generated files."""
        return self.metadata.get('name') or minecraft_name(self.metadata.get('id', 'model'))

    @classmethod
    def from_file(cls, file_path):
        """Read a .pdb or .cif/.mmcif file."""
        if file_path.lower().endswith(('.cif', '.mmcif')):
            return cls.from_mmcif(file_path)
        return cls.from_pdb(file_path)

    @staticmethod
    def _atom_dict(atom_num, atom_name, residue, chain, resid, x, y, z, element, hetatm):
        return {
            'atom_num': atom_num,
            'name': atom_name,
            'atom': atom_name,
            'residue': residue,
            'chain': chain,
            'res_id': resid,
            'resid': resid,
            'x': x,
            'y': y,
            'z': z,
            'element': element,
            'hetatm': hetatm
        }

    def _build_sequences(self):
        chain_residues = {}
        for atom in self.atoms:
            seq = chain_residues.setdefault(atom['chain'], [])
            resid = atom['resid']  # true residue id from the file
            # Only add first atom for each residue, and only amino acids / nucleotides
            if not seq or seq[-1][0] != resid:
                code = three_to_one(atom['residue'])
                if code != '?':
                    seq.append((resid, code))
        self.sequences = chain_residues

    @classmethod
    def from_pdb(cls, file_path):
        instance = cls()
        pdb_id = None
        structural_rows = []
        cmpnd_lines = []
        conect = []
        links = []
        altlocs = _AltlocFilter()
        model_count = 0
        atoms_done = False
        serial_to_atom = {}

        with open(file_path) as f:
            for line in f:
                record = line[:6]
                if record in ('ATOM  ', 'HETATM'):
                    if atoms_done:
                        continue
                    hetatm = record == 'HETATM'
                    atom_name = line[12:16].strip()
                    chain = line[21].strip()
                    resid = int(line[22:26])
                    if not altlocs.keep((chain, resid, line[26]), line[16]):
                        continue
                    element = line[76:78].strip().upper() if len(line) >= 78 else ''
                    if not element:
                        element = _infer_pdb_element(line, hetatm)
                    # Ignore hydrogens
                    if element in HYDROGEN_ELEMENTS:
                        continue
                    try:
                        atom_num = int(line[6:11])
                    except ValueError:  # hybrid-36 serials in very large files
                        atom_num = len(instance.atoms) + 1
                    atom = cls._atom_dict(atom_num, atom_name, line[17:20].strip(), chain, resid,
                                          float(line[30:38]), float(line[38:46]), float(line[46:54]),
                                          element, hetatm)
                    instance.atoms.append(atom)
                    serial_to_atom.setdefault(atom_num, atom)
                elif record == 'MODEL ':
                    model_count += 1
                    # Only the first model of multi-model (e.g. NMR) files is used
                    atoms_done = model_count > 1
                elif record == 'ENDMDL':
                    atoms_done = True
                elif record == 'CONECT':
                    conect.append(line)
                elif record == 'LINK  ':
                    try:
                        links.append(((line[21].strip(), int(line[22:26]), line[12:16].strip()),
                                      (line[51].strip(), int(line[52:56]), line[42:46].strip())))
                    except (ValueError, IndexError):
                        pass
                elif record == 'HEADER':
                    instance.metadata['header'] = line[10:].strip()
                    if len(line) >= 66:
                        pdb_id = line[62:66].strip() or None
                elif record == 'TITLE ':
                    instance.metadata['title'] = instance.metadata.get('title', '') + line[10:].strip() + ' '
                elif record == 'AUTHOR':
                    instance.metadata['author'] = instance.metadata.get('author', '') + line[10:].strip() + ' '
                elif line.startswith("REMARK   2 RESOLUTION."):
                    instance.metadata['resolution'] = line[22:].strip()
                elif record == 'EXPDTA':
                    instance.metadata['experimental_method'] = line[10:].strip()
                elif record == 'COMPND':
                    cmpnd_lines.append(line[10:].strip())
                elif record == 'HELIX ':
                    structural_rows.append([line[19].strip(), line[15:18].strip(), line[21:25].strip(),
                                            line[27:30].strip(), line[33:37].strip(), 'helix'])
                elif record == 'SHEET ':
                    structural_rows.append([line[21].strip(), line[17:20].strip(), line[22:26].strip(),
                                            line[28:31].strip(), line[33:37].strip(), 'sheet'])

        instance.structural_info = _clean_structural_info(structural_rows)

        # CONECT bonds; keep a bond if either atom is a HETATM
        seen = set()
        for line in conect:
            fields = line.split()
            if len(fields) < 3:
                continue
            try:
                src = int(fields[1])
            except ValueError:
                continue
            src_atom = serial_to_atom.get(src)
            if src_atom is None:
                continue
            for tgt_str in fields[2:]:
                try:
                    tgt = int(tgt_str)
                except ValueError:
                    continue
                tgt_atom = serial_to_atom.get(tgt)
                if tgt_atom is None or src == tgt or not (src_atom['hetatm'] or tgt_atom['hetatm']):
                    continue
                # CONECT lists each bond from both ends; keep it once
                pair = (min(src, tgt), max(src, tgt))
                if pair not in seen:
                    seen.add(pair)
                    instance.bonds.append({'atom_num1': src, 'atom_num2': tgt})
        instance.bonds = complete_hetatm_bonds(instance.atoms, instance.bonds, links)

        instance._build_sequences()
        stem = os.path.splitext(os.path.basename(file_path))[0]
        instance.metadata['id'] = pdb_id if pdb_id else stem
        instance.metadata['name'] = minecraft_name(stem)
        instance.metadata['source_file'] = file_path
        instance.chain_identity = cls._parse_compnd(cmpnd_lines)
        return instance

    @staticmethod
    def _parse_compnd(cmpnd_lines):
        chain_identity = {}
        if not cmpnd_lines:
            return chain_identity
        full = " ".join(cmpnd_lines)
        # split into fields by semicolon; keep order
        tokens = [t.strip() for t in full.split(";") if t.strip()]

        current_molecule = None
        for token in tokens:
            # MOLECULE: <name>
            m = re.match(r'^\s*MOLECULE:\s*(.+)$', token, flags=re.I)
            if m:
                # remove any trailing commas or periods
                current_molecule = m.group(1).strip().rstrip(".,")
                continue

            # CHAIN: A, B, C
            c = re.match(r'^\s*CHAIN:\s*(.+)$', token, flags=re.I)
            if c and current_molecule:
                chains = [ch.strip() for ch in c.group(1).split(",") if ch.strip()]
                for ch in chains:
                    chain_identity[ch] = current_molecule
                # consume the molecule so only the first CHAIN is associated with it
                current_molecule = None
        return chain_identity

    def save_to_file(self, base_path):
        # Save metadata
        with open(f"{base_path}_metadata.txt", "w") as f:
            for key, value in self.metadata.items():
                f.write(f"{key}: {value}\n")
        # Save structural_info DataFrame
        self.structural_info.to_csv(f"{base_path}_structural_info.csv", index=False)
        # Save atoms list
        pd.DataFrame(self.atoms).to_csv(f"{base_path}_atoms.csv", index=False)

    @classmethod
    def from_mmcif(cls, file_path):
        # MMCIF2Dict only tokenises the file; building a full Bio.PDB structure is not needed
        from Bio.PDB.MMCIF2Dict import MMCIF2Dict
        mmcif_dict = MMCIF2Dict(file_path)
        instance = cls()

        def first(key, default=''):
            value = mmcif_dict.get(key, [default])
            value = value[0] if isinstance(value, list) else value
            return '' if value in ('?', '.') else value

        stem = os.path.splitext(os.path.basename(file_path))[0]
        pdb_id = first('_entry.id')
        # Metadata
        instance.metadata['id'] = pdb_id if pdb_id else stem
        instance.metadata['name'] = minecraft_name(stem)
        instance.metadata['header'] = first('_struct.title')
        instance.metadata['title'] = first('_struct.title')
        instance.metadata['author'] = ', '.join(mmcif_dict.get('_audit_author.name', []))
        instance.metadata['resolution'] = first('_refine.ls_d_res_high')
        instance.metadata['experimental_method'] = first('_exptl.method')

        # Secondary structure: helices and sheets
        structural_rows = []
        helix_fields = [
            '_struct_conf.conf_type_id',
            '_struct_conf.beg_auth_asym_id',
            '_struct_conf.beg_auth_comp_id',
            '_struct_conf.beg_auth_seq_id',
            '_struct_conf.end_auth_comp_id',
            '_struct_conf.end_auth_seq_id'
        ]
        if all(field in mmcif_dict for field in helix_fields):
            for conf_type, chain, res1, id1, res2, id2 in zip(*(mmcif_dict[f] for f in helix_fields)):
                if 'HELX' in conf_type:
                    structural_rows.append([chain, res1, id1, res2, id2, 'helix'])
        sheet_fields = [
            '_struct_sheet_range.beg_auth_asym_id',
            '_struct_sheet_range.beg_auth_comp_id',
            '_struct_sheet_range.beg_auth_seq_id',
            '_struct_sheet_range.end_auth_comp_id',
            '_struct_sheet_range.end_auth_seq_id'
        ]
        if all(field in mmcif_dict for field in sheet_fields):
            for chain, res1, id1, res2, id2 in zip(*(mmcif_dict[f] for f in sheet_fields)):
                structural_rows.append([chain, res1, id1, res2, id2, 'sheet'])
        instance.structural_info = _clean_structural_info(structural_rows)

        # Parse atoms
        atom_ids = mmcif_dict.get('_atom_site.id', [])
        n = len(atom_ids)

        def column(key, fallback=None):
            values = mmcif_dict.get(key)
            if values is None and fallback is not None:
                values = mmcif_dict.get(fallback)
            return values if values is not None else ['.'] * n

        atom_names = column('_atom_site.auth_atom_id', '_atom_site.label_atom_id')
        res_names = column('_atom_site.auth_comp_id', '_atom_site.label_comp_id')
        chains = column('_atom_site.auth_asym_id', '_atom_site.label_asym_id')
        auth_res_ids = column('_atom_site.auth_seq_id')
        label_res_ids = column('_atom_site.label_seq_id')
        label_asym_ids = column('_atom_site.label_asym_id')
        ins_codes = column('_atom_site.pdbx_PDB_ins_code')
        alt_ids = column('_atom_site.label_alt_id')
        models = column('_atom_site.pdbx_PDB_model_num')
        x_coords = mmcif_dict.get('_atom_site.Cartn_x', [])
        y_coords = mmcif_dict.get('_atom_site.Cartn_y', [])
        z_coords = mmcif_dict.get('_atom_site.Cartn_z', [])
        elements = column('_atom_site.type_symbol')
        groups = column('_atom_site.group_PDB')

        altlocs = _AltlocFilter()
        first_model = models[0] if n else None
        for i in range(n):
            # Only the first model of multi-model (e.g. NMR) files is used
            if models[i] != first_model:
                continue
            try:
                atom_num = int(atom_ids[i])
            except ValueError:
                continue
            element = elements[i].strip().upper()
            # Ignore hydrogens
            if element in HYDROGEN_ELEMENTS:
                continue
            resid_text = auth_res_ids[i] if auth_res_ids[i] not in ('?', '.') else label_res_ids[i]
            try:
                resid = int(resid_text)
            except ValueError:
                resid = 0
            chain = chains[i].strip()
            if not altlocs.keep((chain, resid, ins_codes[i]), alt_ids[i]):
                continue
            atom = cls._atom_dict(atom_num, atom_names[i].strip(), res_names[i].strip(), chain, resid,
                                  float(x_coords[i]), float(y_coords[i]), float(z_coords[i]),
                                  element, groups[i].strip() == "HETATM")
            atom['label_asym_id'] = label_asym_ids[i].strip()
            instance.atoms.append(atom)

        # Build bonds for HETATMs using _chem_comp_bond templates
        bonds = []
        if '_chem_comp_bond.comp_id' in mmcif_dict:
            # Group HETATM atoms per residue instance, indexed by atom name
            groups_by_comp = {}
            for a in instance.atoms:
                if a['hetatm']:
                    key = (a['chain'], a.get('label_asym_id', ''), a['resid'])
                    groups_by_comp.setdefault(a['residue'], {}).setdefault(key, {}).setdefault(a['atom'], []).append(a)
            for comp_id, atom1, atom2 in zip(mmcif_dict['_chem_comp_bond.comp_id'],
                                             mmcif_dict['_chem_comp_bond.atom_id_1'],
                                             mmcif_dict['_chem_comp_bond.atom_id_2']):
                for by_name in groups_by_comp.get(comp_id, {}).values():
                    for a1 in by_name.get(atom1, ()):
                        for a2 in by_name.get(atom2, ()):
                            if a1['atom_num'] != a2['atom_num']:
                                bonds.append({'atom_num1': a1['atom_num'], 'atom_num2': a2['atom_num']})

        # Covalent links (the mmCIF version of PDB LINK records)
        links = []
        conn_fields = ['_struct_conn.conn_type_id',
                       '_struct_conn.ptnr1_auth_asym_id', '_struct_conn.ptnr1_auth_seq_id',
                       '_struct_conn.ptnr1_label_atom_id',
                       '_struct_conn.ptnr2_auth_asym_id', '_struct_conn.ptnr2_auth_seq_id',
                       '_struct_conn.ptnr2_label_atom_id']
        if all(field in mmcif_dict for field in conn_fields):
            for kind, c1, r1, n1, c2, r2, n2 in zip(*(mmcif_dict[f] for f in conn_fields)):
                if not kind.lower().startswith('covale'):
                    continue
                try:
                    links.append(((c1, int(r1), n1), (c2, int(r2), n2)))
                except ValueError:
                    continue
        instance.bonds = complete_hetatm_bonds(instance.atoms, bonds, links)

        instance._build_sequences()
        instance.metadata['source_file'] = file_path

        # Map chains to molecule names via their entity id
        entity_names = dict(zip(mmcif_dict.get('_entity.id', []), mmcif_dict.get('_entity.pdbx_description', [])))
        entity_names.update(zip(mmcif_dict.get('_entity_name_com.entity_id', []),
                                mmcif_dict.get('_entity_name_com.name', [])))
        chain_identity = {}
        for eid, strands in zip(mmcif_dict.get('_entity_poly.entity_id', []),
                                mmcif_dict.get('_entity_poly.pdbx_strand_id', [])):
            name = entity_names.get(eid, "")
            name = "" if name in ('?', '.') else name
            for c in strands.replace(" ", "").split(","):
                if c:
                    chain_identity[c] = name
        instance.chain_identity = chain_identity
        return instance
