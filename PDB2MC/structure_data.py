from Bio.PDB import PDBParser, MMCIFParser
from Bio.PDB.Polypeptide import is_aa
import pandas as pd

# Helper function for nucleic acid detection
NUCLEOTIDE_CODES = {'A', 'C', 'G', 'T', 'U', 'DA', 'DC', 'DG', 'DT', 'DU', 'ADE', 'CYT', 'GUA', 'THY', 'URA'}

def is_nucleotide_residue(residue):
    return residue.get_resname().strip().upper() in NUCLEOTIDE_CODES

class StructureData:
    def __init__(self):
        self.atoms = []
        self.metadata = {}
        self.structural_info = pd.DataFrame(
            columns=['chain', 'residue1', 'resid1', 'residue2', 'resid2', 'structure']
        )
        self.sequences = {}  # chain_id: list of codes

    @classmethod
    def from_pdb(cls, file_path):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure('structure', file_path)
        instance = cls()
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
        # Parse atoms
        for model in structure:
            for chain in model:
                seq = []
                for residue in chain:
                    if is_aa(residue, standard=True):
                        seq.append(residue.get_resname())
                    elif is_nucleotide_residue(residue):
                        # Use 1-letter code for nucleic acids (A, T, G, C, U)
                        seq.append(residue.get_resname().strip()[-1])
                    hetatm = residue.id[0].strip() != ""
                    for atom in residue:
                        instance.atoms.append({
                            'name': atom.get_name(),
                            'residue': residue.get_resname(),
                            'chain': chain.id,
                            'res_id': residue.id[1],
                            'x': atom.coord[0],
                            'y': atom.coord[1],
                            'z': atom.coord[2],
                            'element': atom.element,
                            'hetatm': hetatm
                        })
                if seq:
                    instance.sequences[chain.id] = seq
        instance.metadata['id'] = structure.id
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
        structure = parser.get_structure('structure', file_path)
        instance = cls()

        # Parse mmCIF dictionary for metadata and secondary structure
        mmcif_dict = parser._mmcif_dict
        # Metadata
        instance.metadata['id'] = structure.id
        instance.metadata['header'] = mmcif_dict.get('_struct.title', [''])[0]
        instance.metadata['title'] = mmcif_dict.get('_struct.title', [''])[0]
        instance.metadata['author'] = ', '.join(mmcif_dict.get('_audit_author.name', []))
        instance.metadata['resolution'] = mmcif_dict.get('_refine.ls_d_res_high', [''])[0]
        instance.metadata['experimental_method'] = mmcif_dict.get('_exptl.method', [''])[0]

        # Secondary structure: helices and sheets
        # Helices
        if '_struct_conf.conf_type_id' in mmcif_dict:
            for i, conf_type in enumerate(mmcif_dict['_struct_conf.conf_type_id']):
                if 'HELX' in conf_type:
                    data = {
                        'chain': mmcif_dict['_struct_conf.pdbx_PDB_strand_id'][i].split(',')[0].strip(),
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
        if '_struct_sheet_range.sheet_id' in mmcif_dict:
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
        for model in structure:
            for chain in model:
                seq = []
                for residue in chain:
                    if is_aa(residue, standard=True):
                        seq.append(residue.get_resname())
                    elif is_nucleotide_residue(residue):
                        seq.append(residue.get_resname().strip()[-1])
                    hetatm = residue.id[0].strip() != ""
                    for atom in residue:
                        instance.atoms.append({
                            'name': atom.get_name(),
                            'residue': residue.get_resname(),
                            'chain': chain.id,
                            'res_id': residue.id[1],
                            'x': atom.coord[0],
                            'y': atom.coord[1],
                            'z': atom.coord[2],
                            'element': atom.element,
                            'hetatm': hetatm
                        })
                if seq:
                    instance.sequences[chain.id] = seq
        return instance