import pandas as pd
import os
#import tkinter as tk
#from tkinter import filedialog
import numpy as np
import math
from scipy.interpolate import splprep, splev
#from scipy.spatial import ConvexHull, Delaunay, cKDTree
from scipy import ndimage
#import tifffile as tiff
from scipy.ndimage import convolve
from scipy.spatial import cKDTree
import sys
from functools import lru_cache
from PDB2MC.structure_data import StructureData
from PDB2MC import resources

import logging


@lru_cache(maxsize=4)
def _load_structure_cached(file_path, mtime):
    return StructureData.from_file(file_path)


def load_structure(file_path):
    """
    Read a PDB/mmCIF file into a StructureData, reusing the result if the same unchanged file
    was read recently (selecting a file, checking its size and generating the model all need it).
    Treat the returned object as read-only.
    """
    file_path = os.path.abspath(file_path)
    return _load_structure_cached(file_path, os.path.getmtime(file_path))


def structure_to_df(structure):
    """Coordinate DataFrame (X, Y, Z, atom, residue, chain, resid, element, row, ...) for a StructureData."""
    df = pd.DataFrame(structure.atoms)
    if df.empty:
        return pd.DataFrame(columns=['atom_num', 'atom', 'residue', 'chain', 'resid', 'X', 'Y', 'Z', 'element', 'row'])
    df = df.rename(columns={'x': 'X', 'y': 'Y', 'z': 'Z'})
    df['row'] = np.where(df['hetatm'], 'HETATM', 'ATOM')
    df['atom'] = df['atom'].astype(str)
    return df


# Function that takes a pdb file, reads the coordinates of a single chain, and determines whether the shortest edge of the bounding box is shorter than the parameter ymax
def _model_height(file_path):
    """Height (Y extent, in Angstrom = blocks at scale 1) of a model after rotate_to_y puts its smallest side on Y."""
    structure = file_path if isinstance(file_path, StructureData) else load_structure(file_path)
    df = structure_to_df(structure)
    if df.empty:
        return 0.0
    ranges = df[['X', 'Y', 'Z']].max() - df[['X', 'Y', 'Z']].min()
    return float(ranges.min())


def check_model_size(file_path, world_max):
    """True if the model (a path or StructureData) fits in world_max blocks of height at scale 1."""
    try:
        return _model_height(file_path) < world_max
    except Exception as e:
        print(f"Error in check_model_size: {e}")
        return False


def check_max_size(file_path, world_max):
    """
    Largest protein scale at which the model still fits in world_max blocks of height,
    rounded down to one decimal (the precision of the scale spin boxes).
    """
    try:
        height = _model_height(file_path)
        if height <= 0:
            return 1
        return max(1.0, math.floor(world_max / height * 10) / 10)
    except Exception as e:
        print(f"Error in check_max_size: {e}")
        return 1


def read_pdb(filename_or_structure):
    if isinstance(filename_or_structure, str):
        atom_data = []
        with open(filename_or_structure, 'r') as f:
            for line in f:
                if line.startswith('ATOM') or line.startswith("HETATM"):
                    record = {'row': line[0:6].strip(),
                              'atom_num': line[6:11].strip(),
                              'atom': line[12:16].strip(),
                              'residue': line[17:20].strip(),
                              #'chain': line[21],
                              'chain': line[20:22].strip(),
                              'resid': int(line[22:26]),
                              'X': pd.to_numeric(line[30:38].strip()),
                              'Y': pd.to_numeric(line[38:46].strip()),
                              'Z': pd.to_numeric(line[46:54].strip())}
                    # Check if the current record is the same as the last one in atom_data
                    if not atom_data or (atom_data[-1]['row'] != record['row'] or
                                         atom_data[-1]['atom'] != record['atom'] or
                                         atom_data[-1]['residue'] != record['residue'] or
                                         atom_data[-1]['chain'] != record['chain'] or
                                         atom_data[-1]['resid'] != record['resid']):
                        atom_data.append(record)
                    #atom_data.append(record)
        pdb_df = pd.DataFrame(atom_data)

        return pdb_df
    elif hasattr(filename_or_structure, 'atoms'):
        # StructureData object
        df = pd.DataFrame(filename_or_structure.atoms)
        # Ensure 'resid' column exists and is int
        if 'resid' not in df.columns and 'res_id' in df.columns:
            df['resid'] = df['res_id']
        if 'resid' in df.columns:
            df['resid'] = df['resid'].astype(int)
        return df
    else:
        raise ValueError("Input must be a filename or StructureData object")


def get_pdb_code(file_path):
    code = None
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('HEADER'):
                code = line.strip().split()[-1]
                return code
    if code == None:
        code = 'UNKN'
        return code
    return None


# Scan a dataframe and if there is a column named "chain" return a list of unique values in that column
def enumerate_chains(dataframe):
    if 'chain' in dataframe.columns:
        return dataframe['chain'].unique()
    else:
        return None


# Take a dataframe and if it has a column named "chain", return a dataframe with only the rows that have a matching "chain" value
def get_chain(dataframe, chain):
    if 'chain' in dataframe.columns:
        return dataframe.loc[dataframe['chain'] == chain]
    else:
        return None

# Function to determine if the 3D points provided are a flat plane
# def is_flat(points_3d):
#     x_values, y_values, z_values = points_3d.T
#     return len(set(x_values)) == 1 or len(set(y_values)) == 1 or len(set(z_values)) == 1


def clip_coords(dataframe):
    tmp_df = dataframe[['atom', 'X', 'Y', 'Z']].copy()
    tmp_df[['X', 'Y', 'Z']] = tmp_df[['X', 'Y', 'Z']].astype(float)
    return tmp_df


# Function that takes a dataframe of coordinates, finds the minimum Y value, sets that to -60, and then subtracts that value from all Y values
def set_min_y(df):
    min_y = df['Y'].min()
    df['Y'] = df['Y'] - min_y
    return df


# Function that takes a dataframe of coordinates and a integer, "width", and returns a dataframe of vectors calculated as the vector between each dataframe row with "atom" value of "C" to the next row with matching "resid" and "atom" value of "O".
def CO_vectors(df, width=1):

    # Filter the dataframe for rows with an 'atom' column value of "C" or "O"
    df = df[df['atom'].isin(['C', 'O'])]
    df = df.reset_index(drop=True)

    # Create an empty list to store the coordinates
    coordinates = []

    # Ensure that width is an integer:
    # width = int(width)

    # Iterate over the rows of the dataframe and calculate the vector between the coordinates of each 'C' and 'O' with matching 'resid' values
    for i, row in df.iterrows():
        # Calculate the 3D vector of row i and row i+1
        if i < len(df) - 1:
            if row['atom'] == 'C' and df['atom'][i + 1] == 'O' and row['resid'] == df['resid'][i + 1]:
                coordinates.append([df['X'].values[i + 1] - row['X'], df['Y'].values[i + 1] - row['Y'],
                                    df['Z'].values[i + 1] - row['Z'], row['resid'], row['residue'], row['chain']])

    # multiply the vector by the width
    coordinates = [[coordinates[i][j] * width for j in range(3)] + coordinates[i][3:] for i in range(len(coordinates))]

    # Create a new dataframe with the new coordinates
    new_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain'])
    return new_df


# Function that will take the coordinates from a dataframe, match them with the vectors of another dataframe by "resid" column, and make two dataframes of each coordinate transformed by either the positive or negative of the matched vector. Then call bresenham_line function to fill the gaps. combine all 3 dataframes and return them.


def flank_coordinates(df, vector_df, bar=False):
    # Build a lookup for vectors by resid
    vector_dict = vector_df.set_index('resid')[['X', 'Y', 'Z']].to_dict('index')
    max_resid = df['resid'].max()

    # Prepare output
    ribbon_rows = []

    # Only process backbone atoms in helix/sheet (unless bar is True)
    for i, row in df.iterrows():
        if row['resid'] < max_resid - 1 and row['atom'] in ('CA', 'C', 'N'):
            if (row['structure'] == 'helix' and not bar) or row['structure'] == 'sheet':
                vector = vector_dict.get(row['resid'])
                if vector is not None:
                    # Positive and negative flank points
                    pos = np.array([row['X'], row['Y'], row['Z']]) + np.array([vector['X'], vector['Y'], vector['Z']])
                    neg = np.array([row['X'], row['Y'], row['Z']]) - np.array([vector['X'], vector['Y'], vector['Z']])
                    # Fill in the ribbon between flanks
                    ribbon_coords = bresenham_line(int(round(neg[0])), int(round(neg[1])), int(round(neg[2])),
                                                   int(round(pos[0])), int(round(pos[1])), int(round(pos[2])))
                    for x, y, z in ribbon_coords:
                        ribbon_rows.append({
                            'atom_num': row['atom_num'],
                            'atom': row['atom'],
                            'residue': row['residue'],
                            'resid': row['resid'],
                            'chain': row['chain'],
                            'X': x,
                            'Y': y,
                            'Z': z
                        })
    # Return as DataFrame
    if ribbon_rows:
        return pd.DataFrame(ribbon_rows, columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])
    else:
        return pd.DataFrame(columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])


# Function that takes a dataframe of coordinates and a integer, "width", and returns a dataframe of vectors calculated as the vector between each dataframe row with "atom" value of "C" to the next row with matching "resid" and "atom" value of "O".
def DNA_vectors(df, width=1):
    # Filter the dataframe for rows with an 'atom' column value of "OP1" or "OP2"
    df = df[df['atom'].isin(['OP1', 'P'])]
    df = df.reset_index(drop=True)

    # Create an empty list to store the coordinates
    coordinates = []

    # Iterate over the rows of the dataframe and calculate the vector between the coordinates of each 'C' and 'O' with matching 'resid' values
    for i, row in df.iterrows():

        # Calculate the 3D vector of row i and row i+1
        if i < len(df) - 1:

            if row['atom'] == 'P' and df['atom'][i + 1] == 'OP1' and row['resid'] == df['resid'][i + 1]:
                coordinates.append([df['X'].values[i + 1] - row['X'], df['Y'].values[i + 1] - row['Y'],
                                    df['Z'].values[i + 1] - row['Z'], row['resid'], row['residue'], row['chain']])

    # multiply the vector by the width
    coordinates = [[coordinates[i][j] * width for j in range(3)] + coordinates[i][3:] for i in range(len(coordinates))]

    # Create a new dataframe with the new coordinates
    new_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain'])

    return new_df


# TODO

# Function that will take the coordinates from a dataframe, match them with the vectors of another dataframe by "resid" column, and make two dataframes of each coordinate transformed by either the positive or negative of the matched vector. Then call bresenham_line function to fill the gaps. combine all 3 dataframes and return them.
def flank_DNA(df, vector_df):
    # Create an empty list to store the positive coordinates
    positive_coordinates = []

    # Create an empty list to store the negative coordinates
    negative_coordinates = []

    # Create an empty list to store the non-flanked coordinates
    non_flanked_coordinates = []

    vector_iter_count = 1
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z"]

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        #if df.loc[i, 'resid'] < df['resid'].max() - 1:
        if df.loc[i, 'resid'] <= df['resid'].max():
            # Find the matching row in the vector dataframe
            matching_vector = vector_df[vector_df['resid'] == row['resid']]

            # subset df by rows that match the current row's resid
            match_len = len(df[df['resid'] == row['resid']])

            # Find the next row in the vector dataframe
            next_vector = vector_df[vector_df['resid'] == row['resid'] + 1]

            backbone_atoms = ["O5'", "C5'", "C4'", "C3'", "O3'"]
            #backbone_atoms = ["C4'", "C3'"]
            # Iterate over the matching vector rows
            for j, vector_row in matching_vector.iterrows():

                #Check if row['atom'] is a backbone atom
                if row['atom'] in backbone_atoms:

                    # Add the positive coordinates to the positive coordinates list
                    positive_coordinates.append(
                        [row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'],
                         row['X'] + vector_row['X'], row['Y'] + vector_row['Y'], row['Z'] + vector_row['Z']])

                    # Add the negative coordinates to the negative coordinates list
                    negative_coordinates.append(
                        [row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'],
                         row['X'] - vector_row['X'], row['Y'] - vector_row['Y'], row['Z'] - vector_row['Z']])

                else:
                    continue
            if vector_iter_count > match_len:
                vector_iter_count = 1
            else:
                vector_iter_count += 1

    # Create a new dataframe with the positive coordinates
    positive_df = pd.DataFrame(positive_coordinates,
                               columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    # Create a new dataframe with the negative coordinates
    negative_df = pd.DataFrame(negative_coordinates,
                               columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    # Create a new dataframe with the non-flanked coordinates
    non_flanked_df = pd.DataFrame(non_flanked_coordinates,
                                  columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    # Ensure all the values in the X, Y, Z columns are integers
    positive_df['X'] = positive_df['X'].astype(int)
    positive_df['Y'] = positive_df['Y'].astype(int)
    positive_df['Z'] = positive_df['Z'].astype(int)

    negative_df['X'] = negative_df['X'].astype(int)
    negative_df['Y'] = negative_df['Y'].astype(int)
    negative_df['Z'] = negative_df['Z'].astype(int)

    non_flanked_df['X'] = non_flanked_df['X'].astype(int)
    non_flanked_df['Y'] = non_flanked_df['Y'].astype(int)
    non_flanked_df['Z'] = non_flanked_df['Z'].astype(int)

    # Round the coordinates to the nearest whole number
    positive_df = positive_df.round()
    negative_df = negative_df.round()
    non_flanked_df = non_flanked_df.round()

    # iterate through each dataframe and call the bresenham_line function to fill in the gaps between each coordinate, add the new coordinates to a new dataframe, and return the new dataframe
    for i, row in positive_df.iterrows():

        # assume that positive_df and negative_df have the same number of rows and order of rows

        new_coordinates = bresenham_line(negative_df['X'][i], negative_df['Y'][i], negative_df['Z'][i], row['X'],
                                         row['Y'], row['Z'])
        new_coordinates = bresenham_line(negative_df['X'][i], negative_df['Y'][i], negative_df['Z'][i], row['X'],
                                         row['Y'], row['Z'])
        new_df = pd.DataFrame(new_coordinates, columns=['X', 'Y', 'Z'])
        new_df['resid'] = row['resid']
        new_df['residue'] = row['residue']
        new_df['chain'] = row['chain']
        new_df['atom_num'] = row['atom_num']
        new_df['atom'] = row['atom']
        if i == 0:
            final_df = new_df
        else:
            final_df = pd.concat([final_df, new_df], ignore_index=True)

    # reorder the columns
    columns = ["atom_num", "atom", "residue", "resid", "chain", "X", "Y", "Z"]
    final_df = final_df[columns]

    return final_df


# Function that takes a dataframe of coordinates and finds the max and min values for X, Y, and Z, then assumes that is a box, then rotates the coordinates such that the smallest dimension of the box is now the Y axis. Returns a dataframe of the transformed coordinates.
def rotate_to_y(df):
    min_x = df['X'].min()
    max_x = df['X'].max()
    min_y = df['Y'].min()
    max_y = df['Y'].max()
    min_z = df['Z'].min()
    max_z = df['Z'].max()
    x_range = max_x - min_x
    y_range = max_y - min_y
    z_range = max_z - min_z

    if x_range < y_range and x_range < z_range:
        df = rotate_x(df)
    if y_range < x_range and y_range < z_range:
        df = rotate_y(df)
    if z_range < x_range and z_range < y_range:
        df = rotate_z(df)

    df = set_min_y(df)

    return df


def interpolate_dataframe(df, smoothness):
    # Check if there is an 'atom' column in the dataframe
    if 'atom' in df.columns:
        # Test if there are more than just backbone atoms (CA, C, N) in the dataframe, if so, split the dataframe into two dataframes, one with just backbone atoms and one with all atoms
        if len(df['atom'].unique()) >= 2:
            #other_df = df[~df['atom'].isin(['CA', 'C', 'N', "C3'", "C4'", "C5'", "O3'", "O5'", "P"])]
            #backbone_df = df[df['atom'].isin(['CA', 'C', 'N', "C3'", "C4'", "C5'", "O3'", "O5'", "P"])]
            other_df = df[~df['atom'].isin(['CA', 'C', 'N', "C3'", "C4'"])]
            backbone_df = df[df['atom'].isin(['CA', 'C', 'N', "C3'", "C4'"])]
            # Reset row number
            backbone_df = backbone_df.reset_index(drop=True)
        else:
            backbone_df = df
    else:
        backbone_df = df
        # Create an empty other_df with columns that match df
        other_df = pd.DataFrame(columns=df.columns)

    # Only select columns 'X', 'Y', and 'Z'
    backbone_coord_df = backbone_df[['X', 'Y', 'Z']]

    # Make a dataframe of the values that are not in the 'X', 'Y', and 'Z' columns from backbone_df
    backbone_extra_columns_df = backbone_df.drop(columns=['X', 'Y', 'Z'])

    # Extract X, Y, Z coordinates
    points = backbone_coord_df[['X', 'Y', 'Z']].values.T

    # Check if the points are floats, if not convert them to floats
    if points.dtype != 'float64':
        points = points.astype(float)
        points = points + 0.01
    else:
        # Add a decimal to the points if they don't have one
        points = points + 0.01
    point_len = len(points[0])

    # Perform B-spline interpolation
    tck, _ = splprep(points, s=smoothness)

    # Generate interpolated points
    u = np.linspace(0, 1, num=point_len)  # Increase num for more interpolated points
    interpolated_points = splev(u, tck)

    # Create a new dataframe with interpolated points
    interpolated_df = pd.DataFrame(
        {'X': interpolated_points[0], 'Y': interpolated_points[1], 'Z': interpolated_points[2]}
    )
    # Round the coordinates to the nearest whole number
    interpolated_df = interpolated_df.round()

    # Add the remaining columns back to the interpolated dataframe
    interpolated_df = pd.concat([interpolated_df, backbone_extra_columns_df], axis=1)

    # Re-order the columns of interpolated_df to match the original dataframe, df
    interpolated_df = interpolated_df[df.columns]

    # Concatenate the interpolated_df with the other_df and order them by the resid then atom_num
    if 'atom' in df.columns:
        if len(df['atom'].unique()) > 3:
            interpolated_df = pd.concat([interpolated_df, other_df], axis=0)
            interpolated_df = interpolated_df.sort_values(by=['resid', 'atom_num'])
            interpolated_df = interpolated_df.reset_index(drop=True)
        else:
            interpolated_df = pd.concat([interpolated_df, other_df], axis=0)
    else:
        interpolated_df = pd.concat([interpolated_df, other_df], axis=0)

    return interpolated_df


# The rotate_* functions must be proper rotations (determinant +1). A reflection would turn the model
# into its mirror image: right-handed helices become left-handed and L-amino acids become D.
# Minecraft's axes (X east, Y up, Z south) are right-handed like PDB coordinates.
def rotate_x(df):
    """Rotate so the old X axis becomes Y: (x, y, z) -> (z, x, y)."""
    x, y, z = df['X'].to_numpy(copy=True), df['Y'].to_numpy(copy=True), df['Z'].to_numpy(copy=True)
    df['X'] = z
    df['Y'] = x
    df['Z'] = y
    return df


def rotate_y(df):
    """Quarter turn about Y: (x, y, z) -> (z, y, -x)."""
    x, y, z = df['X'].to_numpy(copy=True), df['Y'].to_numpy(copy=True), df['Z'].to_numpy(copy=True)
    df['X'] = z
    df['Y'] = y
    df['Z'] = -x
    return df


def rotate_z(df):
    """Rotate so the old Z axis becomes Y: (x, y, z) -> (y, z, x)."""
    x, y, z = df['X'].to_numpy(copy=True), df['Y'].to_numpy(copy=True), df['Z'].to_numpy(copy=True)
    df['X'] = y
    df['Y'] = z
    df['Z'] = x
    return df


def move_coordinates(df):
    first_row = df.iloc[0]
    coords_df = df[['X', 'Y', 'Z']]
    coords_df -= first_row[['X', 'Y', 'Z']]
    df[['X', 'Y', 'Z']] = coords_df
    return df


def calculate_vectors(pdb_df):
    coords = pdb_df[['X', 'Y', 'Z']].values.astype(float)
    diffs = np.diff(coords, axis=0)
    vectors = np.insert(diffs, 0, np.nan, axis=0)
    vector_df = pd.DataFrame(vectors, columns=['dX', 'dY', 'dZ'])
    vector_df.iloc[0] = [0, 0, 0]
    return vector_df


def scale_coordinates(vector_df, scalar):
    # extract the 'atom' column and remove it temporarily
    coords_df = vector_df.loc[:, ['X', 'Y', 'Z']]
    other_df = vector_df.loc[:, ~vector_df.columns.isin(['X', 'Y', 'Z'])]

    # atom_col = vector_df['atom']
    # vector_df = vector_df.drop('atom', axis=1)

    # perform the scalar multiplication on the remaining columns
    scaled_df = coords_df.multiply(scalar, axis='rows')

    # add the 'atom' column back in to the scaled dataframe
    # scaled_df['atom'] = atom_col

    scaled_df = pd.concat([other_df, scaled_df], axis=1, sort=False)
    return scaled_df


def increase_cylinder_diameter(df, diameter):
    # Convert DataFrame to numpy array
    coords = df[['X', 'Y', 'Z']].values

    # Calculate the vector between each point and the next point
    vecs = np.diff(coords, axis=0)

    # Calculate the length of each vector
    lens = np.sqrt(np.sum(vecs ** 2, axis=1))

    # Normalize the vectors
    vecs = vecs / lens[:, np.newaxis]

    # Create a matrix of rotation angles for each vector
    angles = np.arccos(vecs[:, 2])

    # Calculate the sin and cos of each angle
    c = np.cos(angles)
    s = np.sin(angles)

    # Create a matrix of rotation vectors for each vector
    rot_vecs = np.zeros_like(vecs)
    rot_vecs[:, 0] = -vecs[:, 1]
    rot_vecs[:, 1] = vecs[:, 0]

    # Rotate the rotation vectors by the rotation angles
    rot_vecs = rot_vecs * s[:, np.newaxis] + np.cross(rot_vecs, vecs) * c[:, np.newaxis] + vecs * np.sum(
        rot_vecs * vecs, axis=1)[:, np.newaxis] * (1 - c[:, np.newaxis])

    # Create a matrix of rotation matrices
    rot_mats = np.zeros((len(vecs), 3, 3))
    rot_mats[:, 0] = vecs
    rot_mats[:, 1:] = rot_vecs[:, np.newaxis]

    # Create a meshgrid of points in a circle
    n_pts = int(np.ceil(diameter))
    r = np.linspace(-n_pts / 2, n_pts / 2, n_pts)
    xx, yy = np.meshgrid(r, r)
    mask = np.sqrt(xx ** 2 + yy ** 2) <= diameter / 2
    xx = xx[mask]
    yy = yy[mask]
    zz = np.zeros_like(xx)

    # Transform the meshgrid by each rotation matrix
    transformed_points = []
    for i, mat in enumerate(rot_mats):
        xyz = np.vstack((xx, yy, zz))
        transformed_xyz = np.dot(mat, xyz) + coords[i]
        transformed_points.append(transformed_xyz.T)

    # Convert transformed points to a new DataFrame
    new_coords = np.vstack(transformed_points)
    new_df = pd.DataFrame(new_coords, columns=['X', 'Y', 'Z'])

    return new_df


def round_df(vector_df):
    # extract the 'atom' column and remove it temporarily
    # atom_col = df['atom']
    # coords_df = df.drop('atom', axis=1)

    # Filter HETATM lines with "HOH" in the fourth column
    vector_df = vector_df[~((vector_df['row'] == 'HETATM') & (vector_df['residue'] == 'HOH'))]
    coords_df = vector_df.loc[:, ['X', 'Y', 'Z']]
    other_df = vector_df.loc[:, ~vector_df.columns.isin(['X', 'Y', 'Z'])]

    round_df = coords_df.round()
    round_df = round_df.astype(int)

    df = pd.concat([other_df, round_df], axis=1, sort=False)
    return df


def filter_type_atom(df, remove_type=None, remove_atom=None):
    filtered_df = df.copy()

    # Filter by remove_type
    if remove_type:
        if isinstance(remove_type, str):
            remove_type = [remove_type]
        filtered_df = filtered_df[~filtered_df['row'].isin(remove_type)]

    # Filter by remove_atom
    if remove_atom:
        if isinstance(remove_atom, str):
            remove_atom = [remove_atom]
        filtered_df = filtered_df[~filtered_df['atom'].str.startswith(tuple(remove_atom))]

    # Reset index
    filtered_df = filtered_df.reset_index(drop=True)

    return filtered_df


def bresenham_line(x0, y0, z0, x1, y1, z1):
    """Bresenham's line algorithm"""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    dz = abs(z1 - z0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    sz = 1 if z0 < z1 else -1
    x, y, z = x0, y0, z0
    points = []
    if dx >= dy and dx >= dz:
        error_1 = 2 * dy - dx
        error_2 = 2 * dz - dx
        for i in range(dx):
            points.append((x, y, z))
            if error_1 > 0:
                y += sy
                error_1 -= 2 * dx
            if error_2 > 0:
                z += sz
                error_2 -= 2 * dx
            error_1 += 2 * dy
            error_2 += 2 * dz
            x += sx
    elif dy >= dx and dy >= dz:
        error_1 = 2 * dx - dy
        error_2 = 2 * dz - dy
        for i in range(dy):
            points.append((x, y, z))
            if error_1 > 0:
                x += sx
                error_1 -= 2 * dy
            if error_2 > 0:
                z += sz
                error_2 -= 2 * dy
            error_1 += 2 * dx
            error_2 += 2 * dz
            y += sy
    else:
        error_1 = 2 * dy - dz
        error_2 = 2 * dx - dz
        for i in range(dz):
            points.append((x, y, z))
            if error_1 > 0:
                y += sy
                error_1 -= 2 * dz
            if error_2 > 0:
                x += sx
                error_2 -= 2 * dz
            error_1 += 2 * dy
            error_2 += 2 * dx
            z += sz
    return np.array(points)


def atom_subset(df, atoms, ignore_het=False, include=True):
    if include:
        subset = df[df['atom'].isin(atoms)]
    else:
        subset = df[~df['atom'].isin(atoms)]
    if ignore_het:
        subset = subset[~subset['row'].str.contains("HETATM")]
    return subset.reset_index(drop=True)

def process_bars(df, size = 1):
    # Initialize an empty DataFrame to store the results
    result_df = pd.DataFrame(columns=['X', 'Y', 'Z'])
    # Iterate over the rows of the input DataFrame
    for i in range(len(df) - 1):
        if (df.loc[i + 1, 'resid'] - df.loc[i, 'resid']) >= 2:
            # Get the coordinates (X, Y, Z) of the current row and the next row
            start_coords = df.loc[i, ['X', 'Y', 'Z']]
            end_coords = df.loc[i + 1, ['X', 'Y', 'Z']]
            # Run the bresenham_line function on these two points and store the result in a temporary DataFrame
           # line_df = pd.DataFrame(bresenham_line(start_coords['X'], start_coords['Y'], start_coords['Z'], end_coords['X'], end_coords['Y'], end_coords['Z']), columns=['X', 'Y', 'Z'])
            line_array = bresenham_line(int(start_coords['X']),
                                        int(start_coords['Y']),
                                        int(start_coords['Z']),
                                        int(end_coords['X']),
                                        int(end_coords['Y']),
                                        int(end_coords['Z']))
            line_df = pd.DataFrame(line_array, columns=['X', 'Y', 'Z'])

            # Run the cylinderize function on the temporary DataFrame and store the result in another DataFrame
            cylinder_df = pd.DataFrame(cylinderize(line_df, diameter=size), columns=['X', 'Y', 'Z'])
            # Append the result to the result DataFrame
            result_df = pd.concat([result_df, cylinder_df], ignore_index=True)

    # Return the result DataFrame
    return result_df

def find_intermediate_points(replot_df, keep_columns=False, atoms=None, fill_columns=False):
    # Filter atoms if needed
    other_atoms_df = pd.DataFrame(columns=replot_df.columns)
    if atoms:
        other_atoms_df = atom_subset(replot_df, atoms, include=False)
        replot_df = atom_subset(replot_df, atoms, include=True)

    columns = ['X', 'Y', 'Z']
    if keep_columns:
        other_columns = replot_df.columns.drop(columns)
        final_columns = replot_df.columns
    else:
        final_columns = columns

    # Convert to numpy for fast access
    coords = replot_df[columns].to_numpy().astype(int)
    chains = replot_df['chain'].to_numpy() if 'chain' in replot_df.columns else np.repeat(None, len(replot_df))

    # Rasterise each consecutive same-chain pair, recording which source rows every point came from.
    # Building one DataFrame at the end (rather than one per pair) is what keeps this fast.
    point_chunks = []
    row_chunks = []
    for i in range(1, len(replot_df)):
        if chains[i - 1] == chains[i]:
            intermediate_points = bresenham_line(*coords[i - 1], *coords[i])
            if intermediate_points.size > 0:
                point_chunks.append(intermediate_points)
                rows = np.full(len(intermediate_points), i)
                if fill_columns and keep_columns:
                    # first half of the line takes the values of the previous row
                    rows[:len(rows) // 2] = i - 1
                row_chunks.append(rows)

    if point_chunks:
        new_data = pd.DataFrame(np.concatenate(point_chunks), columns=columns)
        if keep_columns:
            source = replot_df.iloc[np.concatenate(row_chunks)].reset_index(drop=True)
            for col in other_columns:
                new_data[col] = source[col].to_numpy()
    else:
        new_data = pd.DataFrame(columns=final_columns)

    if len(other_atoms_df) > 0:
        new_data = pd.concat([new_data, other_atoms_df], ignore_index=True)

    return new_data


@lru_cache(maxsize=1)
def _sidechain_bonds():
    """Intra-residue bond table from chains.txt: columns residue, atom, atom2."""
    return pd.read_csv(resources.package_file('chains.txt'), sep=r'\s+', header=None,
                       names=['residue', 'atom', 'atom2'], engine='python', dtype=str)


def sidechain(atom_df):
    """
    Lines (X, Y, Z, atom) for every bond listed in chains.txt. 'atom' holds the 1-based chain number
    (cycling 1-10 in order of appearance) so callers can colour by chain or overwrite it.
    """
    chains_df = _sidechain_bonds()
    if atom_df.empty:
        return pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])

    # Merge to get all atom/atom2 pairs in the structure
    merged = pd.merge(
        atom_df,
        chains_df,
        left_on=['residue', 'atom'],
        right_on=['residue', 'atom'],
        how='inner'
    )

    # Merge again to get coordinates for atom2
    merged = pd.merge(
        merged,
        atom_df,
        left_on=['residue', 'resid', 'chain', 'atom2'],
        right_on=['residue', 'resid', 'chain', 'atom'],
        suffixes=('_1', '_2'),
        how='inner'
    )

    # Assign chain numbers
    chain_values = atom_df["chain"].unique()
    chain_idx_dict = {chain_value: idx for idx, chain_value in enumerate(chain_values)}
    chain_nums = merged['chain'].map(lambda c: (chain_idx_dict[c] % 10) + 1).to_numpy()

    # Run Bresenham for each pair
    ends = merged[['X_1', 'Y_1', 'Z_1', 'X_2', 'Y_2', 'Z_2']].to_numpy().astype(int)
    point_chunks = []
    atom_chunks = []
    for pair, chain_num in zip(ends, chain_nums):
        coords = bresenham_line(*pair)
        if coords.size:
            point_chunks.append(coords)
            atom_chunks.append(np.full(len(coords), chain_num))
    if not point_chunks:
        return pd.DataFrame(columns=['X', 'Y', 'Z', 'atom'])

    coord_df = pd.DataFrame(np.concatenate(point_chunks), columns=['X', 'Y', 'Z'])
    coord_df['atom'] = np.concatenate(atom_chunks)
    coord_df = coord_df.drop_duplicates().reset_index(drop=True)
    return coord_df


def construct_surface_array(df):
    # min_x, max_x = df['X'].min(), df['X'].max()
    # min_y, max_y = df['Y'].min(), df['Y'].max()
    # min_z, max_z = df['Z'].min(), df['Z'].max()
    #
    # x_range = max_x - min_x
    # y_range = max_y - min_y
    # z_range = max_z - min_z
    #
    # surface_array = np.full((x_range, y_range, z_range), 0, dtype=object)
    #
    # for index, row in df.iterrows():
    #     x, y, z = row['X'] - min_x + 1, row['Y'] - min_y + 1, row['Z'] - min_z + 1
    #     surface_array[x, y, z] = index
    #
    # return surface_array

    # Determine the minimum and maximum coordinates from the DataFrame
    min_x, min_y, min_z = df[['X', 'Y', 'Z']].min()
    max_x, max_y, max_z = df[['X', 'Y', 'Z']].max()

    # Calculate the dimensions for the 3D numpy array
    dim_x = max_x - min_x + 1
    dim_y = max_y - min_y + 1
    dim_z = max_z - min_z + 1

    # Create an empty 3D numpy array filled with zeros
    array_3d = np.zeros((dim_x, dim_y, dim_z), dtype=int)

    # Iterate over the DataFrame rows and fill the array
    for index, row in df.iterrows():
        x, y, z = row['X'] - min_x, row['Y'] - min_y, row['Z'] - min_z
        #array_3d[x, y, z] = index + 1  # Set the value to the row index (starting from 1)
        array_3d[x, y, z] = 255
    return array_3d


def get_hetatm_bond_lines_from_df(atom_df, bonds):
    """
    Given a DataFrame of HETATM atoms and a list of bonds (dicts with atom_num1, atom_num2),
    return a DataFrame of all bond line coordinates.
    """
    if atom_df is None or atom_df.empty or not bonds:
        return pd.DataFrame(columns=['X', 'Y', 'Z'])

    # atom_num -> rounded coordinates (first occurrence wins, as before)
    lookup = atom_df.drop_duplicates(subset='atom_num')
    coords_by_num = dict(zip(lookup['atom_num'].astype(int),
                             np.round(lookup[['X', 'Y', 'Z']].to_numpy(dtype=float)).astype(int)))

    lines = []
    for bond in bonds:
        start = coords_by_num.get(int(bond['atom_num1']))
        end = coords_by_num.get(int(bond['atom_num2']))
        if start is None or end is None:
            continue
        line_coords = bresenham_line(*start, *end)
        if line_coords.size:
            lines.append(line_coords)
    if not lines:
        return pd.DataFrame(columns=['X', 'Y', 'Z'])
    return pd.DataFrame(np.concatenate(lines), columns=['X', 'Y', 'Z'])


def find_border_cells(arr_3d):
    #Make a copy of the array and make the values np.int32
    arr_3d_copy = arr_3d.copy()
    arr_3d_copy = arr_3d_copy.astype(np.int32)

    # Define a shape
    # kernel = np.array([[[0, 1, 0],
    #                     [1, 1, 1],
    #                     [0, 1, 0]],
    #                    [[1, 1, 1],
    #                     [1, 1, 1],
    #                     [1, 1, 1]],
    #                    [[0, 1, 0],
    #                     [1, 1, 1],
    #                     [0, 1, 0]]])

    # Define a 3D kernel for the convolution operation
    kernel = np.ones((3, 3, 3), dtype=np.int32)

    # Perform the convolution operation
    convolved = convolve(arr_3d_copy, kernel, mode='constant', cval=0)

    # Create a boolean mask for cells that are filled (255) and have at least one neighboring cell that is empty (0)
    border_mask = (arr_3d_copy == 255) & (convolved < 255 * 27)

    # Apply the mask to the original array
    border_cells = np.where(border_mask, arr_3d_copy, 0)

    return border_cells


# def filter_dataframe(original_df, surface_array):
#     filtered_indices = [index for index in np.ravel(surface_array) if isinstance(index, int)]
#     filtered_df = original_df.loc[filtered_indices]
#
#     return filtered_df


# Function that takes a dataframe of coordinates of points that represent straight lines and a diameter and returns a dataframe of coordinates of new lines that represent a cylinder with the given diameter
def cylinderize(df, diameter):
    diameter = float(diameter)
    radius = diameter / 2
    # Create an empty list to store the coordinates
    coordinates = []

    # add an extra column to the dataframe named 'atom' and set all values to 'C'
    df['atom'] = 'C'

    # Use the add_sphere_coordinates function to add the coordinates of a sphere to each point in the dataframe
    coord = rasterized_sphere(radius)
    center = sphere_center(radius)
    sphere_coords = add_sphere_coordinates(coord, center, df, mesh=False)

    # remove duplicates from the dataframe
    sphere_coords = sphere_coords.drop_duplicates()

    # remove the extra column named 'atom'
    sphere_coords = sphere_coords.drop(columns=['atom'])

    return sphere_coords


def sphere_center(radius):
    diameter = math.ceil(radius) * 2 | 1
    mid_point = diameter // 2
    center = (mid_point, mid_point, mid_point)
    return (center)


def rasterized_sphere(radius):
    diameter = math.ceil(radius) * 2 | 1
    mid_point = diameter // 2

    center = (mid_point, mid_point, mid_point)
    shape = (diameter, diameter, diameter)

    # Create a 3D grid of integers
    x, y, z = np.indices(shape, dtype=np.float32)

    # Translate the grid to the center of the sphere
    x -= center[0]
    y -= center[1]
    z -= center[2]

    # Calculate the distance from each point in the grid to the center of the sphere
    distance = np.sqrt(x ** 2 + y ** 2 + z ** 2)

    # Create a boolean mask for points inside the sphere
    mask = distance <= radius

    # Convert the boolean mask to a 3D numpy array of integers
    sphere = np.zeros(shape, dtype=np.int32)
    sphere[mask] = 1

    return sphere


## Need to change to mesh_mode, so it can be mesh, shell, or filled.
def add_sphere_coordinates(sphere_array, center, df, mesh=False):
    # Get sphere coordinates relative to center
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    rel_coords = sphere_coords - np.array(center)

    # Compute distances from center for all sphere points
    distances = np.linalg.norm(rel_coords, axis=1)
    radius = math.ceil(sphere_array.shape[0] / 2)
    if mesh:
        mask = np.abs(distances - radius) <= 1
    else:
        mask = np.abs(distances - radius) <= 3
    rel_coords = rel_coords[mask]

    # Broadcast addition to all df rows
    base_coords = df[['X', 'Y', 'Z']].values
    atom_col = df['atom'].values

    # Repeat base coordinates and atom values for each sphere point
    n_points = rel_coords.shape[0]
    repeated_base = np.repeat(base_coords, n_points, axis=0)
    tiled_rel = np.tile(rel_coords, (len(df), 1))
    new_coords = repeated_base + tiled_rel
    new_atoms = np.repeat(atom_col, n_points)

    # Build columns separately; stacking coordinates with the atom labels would turn every number into a string
    new_coords = np.asarray(new_coords, dtype=float).astype(int)
    sphere_df = pd.DataFrame(new_coords, columns=['X', 'Y', 'Z'])
    sphere_df['atom'] = new_atoms
    return sphere_df


def add_structure_from_structured_data(df, structure_data):
    """
    Assigns secondary structure (helix, sheet, none) to each amino acid in df using StructureData.structural_info.
    """
    df = df.copy()
    structure = np.full(len(df), "None", dtype=object)
    structure_df = structure_data.structural_info

    if not structure_df.empty and len(df):
        chains = df['chain'].to_numpy()
        resids = df['resid'].to_numpy().astype(int)
        # Walk the ranges backwards so the first matching range wins, as before
        for chain, start, end, kind in zip(structure_df['chain'].to_numpy()[::-1],
                                           structure_df['resid1'].to_numpy(dtype=int)[::-1],
                                           structure_df['resid2'].to_numpy(dtype=int)[::-1],
                                           structure_df['structure'].to_numpy()[::-1]):
            structure[(chains == chain) & (resids >= start) & (resids <= end)] = kind
    df['structure'] = structure
    return df


def shorten_atom_names(df):
    def shorten_atom(atom):
        if atom.startswith('O') or atom.startswith('N') or atom.startswith('C') or atom.startswith('S'):
            return atom[0]
        else:
            return atom[0:2] if not atom[0:2].isdigit() else atom[0]

    mask = df['row'].isin(['ATOM', 'HETATM'])
    df.loc[mask, 'atom'] = df.loc[mask, 'atom'].astype(str).map(shorten_atom)
    return df


def element_atom_names(df):
    """
    Replace atom names with their element symbol for colouring (e.g. 'CL' -> 'CL', 'CA' calcium -> 'CA',
    'C1' -> 'C'). Name-based shortening misreads ions such as chlorine, calcium or sodium as C/C/N.
    Falls back to shorten_atom_names for rows without an element.
    """
    df = shorten_atom_names(df.copy())
    if 'element' in df.columns:
        element = df['element'].fillna('').astype(str).str.strip().str.upper()
        has_element = element != ''
        df.loc[has_element, 'atom'] = element[has_element]
    return df


def polymer_atom_mask(df):
    """
    True for atoms that belong to the protein / nucleic acid polymer: ATOM records, plus HETATM residues
    that carry a full backbone (modified residues such as selenomethionine, MSE, which
    crystal structures record as HETATM). Without this, every modified residue breaks the backbone.
    """
    is_atom = (df['row'] == 'ATOM').to_numpy()
    het = df[~is_atom]
    if het.empty:
        return is_atom
    keys = ['chain', 'resid', 'residue']
    names = het.groupby(keys)['atom'].agg(set)
    polymer = names[names.map(lambda s: {'N', 'CA', 'C'} <= s or {'P', "C4'", "C3'"} <= s)]
    if polymer.empty:
        return is_atom
    het_keys = pd.MultiIndex.from_frame(df[keys])
    return is_atom | het_keys.isin(polymer.index)


def backbone_segments(df, max_bond=2.5, scale=1.0):
    """
    Label consecutive backbone atoms with a segment id that changes at every chain break, so lines are
    not drawn across missing residues (or from one chain end to an unrelated atom). Two consecutive
    atoms are connected if they are in the same chain and closer than max_bond Angstrom
    (covalent backbone bonds are 1.3-1.6 A). Pass unrounded coordinates scaled by `scale`.
    Returns an array of strings like 'A:0', 'A:1', ...
    """
    if df.empty:
        return np.array([], dtype=object)
    coords = df[['X', 'Y', 'Z']].to_numpy(dtype=float)
    chains = df['chain'].astype(str).to_numpy()
    dist = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    breaks = (dist > max_bond * scale) | (chains[1:] != chains[:-1])
    segment = np.concatenate([[0], np.cumsum(breaks)])
    return np.char.add(np.char.add(chains.astype(str), ':'), segment.astype(str)).astype(object)


def change_mode(config):
    if config["mode"] == "Backbone":
        config["show_atoms"] = False
        config["sidechain"] = False
        config["backbone"] = True
    elif config["mode"] == "Skeleton":
        config["show_atoms"] = False
        config["sidechain"] = True
        config["backbone"] = True
    elif config["mode"] == "Space Filling":
        print(":P")
    elif config["mode"] == "X-ray":
        config["show_atoms"] = True
        config["sidechain"] = True
        config["backbone"] = True
        config["atoms"]["C"] = "black_stained_glass"
        config["atoms"]["N"] = "blue_stained_glass"
        config["atoms"]["O"] = "red_stained_glass"
        config["atoms"]["S"] = "yellow_stained_glass"
        config["atoms"]["P"] = "lime_stained_glass"
        config["atoms"]["other_atom"] = "pink_stained_glass"
    elif config["mode"] == "X-ray Backbone":
        config["show_atoms"] = True
        config["sidechain"] = False
        config["backbone"] = True
        config["atoms"]["C"] = "black_stained_glass"
        config["atoms"]["N"] = "blue_stained_glass"
        config["atoms"]["O"] = "red_stained_glass"
        config["atoms"]["S"] = "yellow_stained_glass"
        config["atoms"]["P"] = "lime_stained_glass"
        config["atoms"]["other_atom"] = "pink_stained_glass"
    elif config["mode"] == "Amino Acids":
        config["sidechain"] = False
        config["backbone"] = True
    return config


# Remove downstream use of process_hetatom; always use get_hetatm_bond_lines_from_df with structure.bonds
