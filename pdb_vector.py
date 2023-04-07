from Bio.PDB import PDBParser
from Bio.PDB.vectors import Vector
import numpy as np

def get_vectors(pdb_df):
    p = PDBParser()
    s = p.get_structure("pdb", pdb_df)
    for chains in s:
        for chain in chains:
            prev_residue = None
            prev_atom = None
            for residue in chain:
                if prev_residue == None:
                    prev_residue = residue
                    continue
                if prev_atom == None:
                    prev_atom = residue['CA']
                    continue
                for atom in residue:
                    if atom.get_name() not in ["N", "CA", "C"]:
                        continue
                    if residue.get_resname() == prev_residue.get_resname():
                        if atom.get_name() == "N":
                            vector = Vector(atom.get_vector()) - Vector(prev_atom.get_vector())
                            yield vector
                        elif atom.get_name() == "CA":
                            vector = Vector(atom.get_vector()) - Vector(residue['N'].get_vector())
                            yield vector
                        elif atom.get_name() == "C":
                            vector = Vector(atom.get_vector()) - Vector(atom['CA'].get_vector())
                            yield vector
                    else:
                        if atom.get_name() == "N":
                            vector = Vector(atom.get_vector()) - Vector(prev_atom['C'].get_vector())
                            yield vector
                        elif atom.get_name() == "CA":
                            vector = Vector(atom.get_vector()) - Vector(prev_atom['N'].get_vector())
                            yield vector
                        elif atom.get_name() == "C":
                            vector = Vector(atom.get_vector()) - Vector(atom['CA'].get_vector())
                            yield vector
                prev_residue = residue
                prev_atom = residue['CA']
