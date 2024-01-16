import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
import math
from scipy.interpolate import splprep, splev
from scipy.spatial import ConvexHull, Delaunay, cKDTree
from scipy import ndimage
import tifffile as tiff
import cv2
from scipy.ndimage import convolve
from scipy.spatial import cKDTree
import pkg_resources
import sys

def assign_atom_values(surface_df, branch_df):
    # Build a k-d tree from branch_df
    tree = cKDTree(branch_df[['X', 'Y', 'Z']].values)

    # For each point in surface_df, find the nearest point(s) in branch_df
    for i, surface_row in surface_df.iterrows():
        dist, indices = tree.query(surface_row[['X', 'Y', 'Z']], k=1, distance_upper_bound=np.inf)
        closest_atoms = branch_df.iloc[indices]['atom']
        #breakpoint()
        # If there are multiple points in branch_df with the same minimum distance, check if they all have the same 'atom' value
        if isinstance(closest_atoms, pd.Series):
            #print(f"Number of unique closest atoms for point {i}: {closest_atoms.nunique()}")
            #if closest_atoms.nunique() == 1:
            surface_df.at[i, 'atom'] = 0
        else:
            #print(f"Closest atom for point {i}: {closest_atoms}")
            #if closest_atoms != surface_df.at[i, 'atom']:
            surface_df.at[i, 'atom'] = closest_atoms

    #print(surface_df.head(), "\n", surface_row.tail())
    return surface_df

def remove_random_rows(df, percent):
    # Calculate the number of rows to keep
    num_rows_to_keep = int(len(df) * (1 - percent / 100))

    # Randomly select rows to keep
    df_sample = df.sample(num_rows_to_keep)

    return df_sample

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

def calculate_centroid(df):
    return df[['X', 'Y', 'Z']].mean()

def shift_dataframe(df, vector):
    df[['X', 'Y', 'Z']] = df[['X', 'Y', 'Z']] - vector
    return df

def align_dataframes(*dfs):
    # Calculate the centroid of the first DataFrame
    target_centroid = calculate_centroid(dfs[0])

    # Align all DataFrames to the target centroid
    for df in dfs[1:]:
        centroid = calculate_centroid(df)
        shift_vector = centroid - target_centroid
        df = shift_dataframe(df, shift_vector)

    return dfs

def add_corner_points(df, corner_points):
    # Create a DataFrame from the corner points
    corner_df = pd.DataFrame(corner_points, columns=['X', 'Y', 'Z'])

    # Add an 'atom' column with the value 'temp'
    corner_df['atom'] = 'temp'

    # For each column in the original DataFrame that is not in the corner DataFrame, add the column with the value 'NA'
    for column in set(df.columns) - set(corner_df.columns):
        corner_df[column] = 'NA'

    # Concatenate the original DataFrame with the corner DataFrame
    df = pd.concat([df, corner_df], ignore_index=True)

    return df

def get_corner_points(df):
    # Find the minimum and maximum coordinates
    min_x, max_x = df['X'].min(), df['X'].max()
    min_y, max_y = df['Y'].min(), df['Y'].max()
    min_z, max_z = df['Z'].min(), df['Z'].max()

    # Create a list of the 8 corner points
    corner_points = [
        (min_x, min_y, min_z),
        (min_x, min_y, max_z),
        (min_x, max_y, min_z),
        (min_x, max_y, max_z),
        (max_x, min_y, min_z),
        (max_x, min_y, max_z),
        (max_x, max_y, min_z),
        (max_x, max_y, max_z)
    ]

    return corner_points

# Function that takes a pdb file, reads the coordinates of a single chain, and determines whether the shortest edge of the bounding box is shorter than the parameter ymax
def check_model_size(file_path, world_max):
    pdb_df = read_pdb(file_path)
    chain = clip_coords(pdb_df)
    chain = rotate_to_y(chain)
    ymin = chain['Y'].min()
    ymax = chain['Y'].max()
    ydiff = ymax - ymin
    if ydiff < world_max:
        return True
    else:
        return False


# Function that takes a pdb file, reads the coordinates of a single chain, determines the shortest edge of the bounding box, and determines the muliplication required to make that >= ymax.
def check_max_size(file_path, world_max):
    pdb_df = read_pdb(file_path)
    #chain = pdb_df.loc[pdb_df['chain'] == 'A']
    #chain = clip_coords(chain)
    chain = clip_coords(pdb_df)
    chain = rotate_to_y(chain)
    ymin = chain['Y'].min()
    ymax = chain['Y'].max()
    ydiff = ymax - ymin
    multiplier = math.ceil(world_max / ydiff)
    return multiplier


def choose_subdir(file_path):
    if not file_path:
        home_dir = os.path.expanduser("~")
        appdata_dir = os.path.join(home_dir, "AppData\Roaming\.minecraft\saves")
        if (os.path.isdir(appdata_dir)):
            file_path = appdata_dir
        else:
            file_path = os.path.expanduser("~")
    else:
        print("Path given")

    root = tk.Tk()
    root.withdraw()
    subdirectory = filedialog.askdirectory(initialdir=file_path)
    return os.path.join(file_path, subdirectory)


def read_pdb(filename):
    atom_data = []
    with open(filename, 'r') as f:
        for line in f:
            if line.startswith('ATOM') or line.startswith("HETATM"):
                record = {'row': line[0:6].strip(),
                          'atom_num': line[6:11].strip(),
                          'atom': line[12:16].strip(),
                          'residue': line[17:20].strip(),
                          'chain': line[21],
                          'resid': int(line[22:26]),
                          'X': pd.to_numeric(line[30:38].strip()),
                          'Y': pd.to_numeric(line[38:46].strip()),
                          'Z': pd.to_numeric(line[46:54].strip())}
                atom_data.append(record)
    pdb_df = pd.DataFrame(atom_data)
    return pdb_df


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
def is_flat(points_3d):
    x_values, y_values, z_values = points_3d.T
    return len(set(x_values)) == 1 or len(set(y_values)) == 1 or len(set(z_values)) == 1

def inside_polygon(x, y, x_coords, y_coords):
    n = len(x_coords)
    inside = False
    j = n - 1

    for i in range(n):
        xi, yi = x_coords[i], y_coords[i]
        xj, yj = x_coords[j], y_coords[j]

        if yi == yj:
            if yi == y and min(xi, xj) <= x <= max(xi, xj):
                return True
            j = i
            continue

        if yi > y != yj and min(yi, yj) <= y <= max(yi, yj):
            if xi == xj or x <= xi + (y - yi) * (xj - xi) / (yj - yi):
                inside = not inside

        j = i

    return inside

def find_interior_points(x_coords, y_coords):
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    interior_points = []
    for x in range(min_x + 1, max_x):
        for y in range(min_y + 1, max_y):
            if inside_polygon(x, y, x_coords, y_coords):
                interior_points.append((x, y))

    return interior_points

# Function to fill in the vectorized grid (taken from a dataframe) of an irregular, planar shape
def fill_grid(dataframe):

    # Take the dataframe X, Y, Z columns and convert them to a numpy array
    points_3d = dataframe[['X', 'Y', 'Z']].to_numpy()

    print("Points 3D: \n", points_3d)

    if is_flat(points_3d):
        print("Points are flat")

        #Take the numpy array and remove the column where all values are the same
        points_2d = np.delete(points_3d, np.where(~points_3d.any(axis=0))[0], axis=1)

        points_inside = find_interior_points(points_2d[:,0], points_2d[:,1])

        #Take points_3d and find the column where all the values are the same. Then copy that value to the points_inside array
        for i in range(len(points_inside)):
            points_inside[i] = np.append(points_inside[i], points_3d[0][np.where(~points_3d.any(axis=0))[0]])


    else:

        hull = ConvexHull(points_3d)

        #Get bounding box of the convex hull
        min_x, min_y, min_z = np.min(points_3d, axis=0)
        max_x, max_y, max_z = np.max(points_3d, axis=0)

        # Create a grid of points within the bounding box
        voxel_size = 1
        grid_x = np.arange(min_x, max_x, voxel_size)
        grid_y = np.arange(min_y, max_y, voxel_size)
        grid_z = np.arange(min_z, max_z, voxel_size)

        #Perform voxelization
        grid = np.zeros((len(grid_x), len(grid_y), len(grid_z)), dtype=bool)

        # Iterate through each point in the grid
        for i, x in enumerate(grid_x):
            for j, y in enumerate(grid_y):
                for k, z in enumerate(grid_z):
                    # Check if the point is in the convex hull
                    point_to_check = np.array([x, y, z])
                    triangulation = Delaunay(hull.points[hull.vertices])
                    is_inside = triangulation.find_simplex(point_to_check) >= 0
                    if is_inside:
                        grid[i, j, k] = True

        #Convert voxels to 3D coordinates of grid points within the shape
        points_inside = []
        for i, x in enumerate(grid_x):
            for j, y in enumerate(grid_y):
                for k, z in enumerate(grid_z):
                    if grid[i, j, k]:
                        points_inside.append([x, y, z])

        points_inside = np.array(points_inside)

        # Convert 3D coordinates to a dataframe with the same columns as the original. If there are missing columns,
        # the data will be copied from an existing row

    print(points_inside)

    # Create a dataframe from the points inside the shape
    df_inside = pd.DataFrame(points_inside, columns = ['X', 'Y', 'Z'])

    # Add the columns from the original dataframe to the new dataframe and copy any missing data from the original
    for column in dataframe.columns:
        if column not in df_inside.columns:
            df_inside[column] = dataframe[column].iloc[0]

    return df_inside

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

    # print(df.tail(n=10))

    # Create an empty list to store the coordinates
    coordinates = []

    # Ensure that width is an integer:
    # width = int(width)

    # print(df['atom'][2])
    # Iterate over the rows of the dataframe and calculate the vector between the coordinates of each 'C' and 'O' with matching 'resid' values
    for i, row in df.iterrows():
        # print(i)
        # Calculate the 3D vector of row i and row i+1
        if i < len(df) - 1:
            # print(row['atom'] == 'C')
            # print(df['atom'][i+1] == 'O')
            # print(row['resid'] == df['resid'].values[i+1])
            if row['atom'] == 'C' and df['atom'][i + 1] == 'O' and row['resid'] == df['resid'][i + 1]:
                coordinates.append([df['X'].values[i + 1] - row['X'], df['Y'].values[i + 1] - row['Y'],
                                    df['Z'].values[i + 1] - row['Z'], row['resid'], row['residue'], row['chain']])
                # print(row['resid'], i, len(df), sep=" ")

    # multiply the vector by the width
    coordinates = [[coordinates[i][j] * width for j in range(3)] + coordinates[i][3:] for i in range(len(coordinates))]

    # Create a new dataframe with the new coordinates
    new_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain'])

    # print("Here's the dataframe of vectors:")
    # print(new_df.tail(n=10))
    return new_df


# Function that will take the coordinates from a dataframe, match them with the vectors of another dataframe by "resid" column, and make two dataframes of each coordinate transformed by either the positive or negative of the matched vector. Then call bresenham_line function to fill the gaps. combine all 3 dataframes and return them.
def flank_coordinates(df, vector_df):
    # Create an empty list to store the positive coordinates
    positive_coordinates = []

    # Create an empty list to store the negative coordinates
    negative_coordinates = []

    # Create an empty list to store the non-flanked coordinates
    non_flanked_coordinates = []

    vector_iter_count = 1
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z", "structure"]

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        if df.loc[i, 'resid'] < df['resid'].max() - 1:
            # Find the matching row in the vector dataframe
            matching_vector = vector_df[vector_df['resid'] == row['resid']]

            # subset df by rows that match the current row's resid
            match_len = len(df[df['resid'] == row['resid']])

            # Find the next row in the vector dataframe
            next_vector = vector_df[vector_df['resid'] == row['resid'] + 1]

            # Iterate over the matching vector rows
            for j, vector_row in matching_vector.iterrows():

                if row['atom'] == 'CA' or row['atom'] == 'C' or row['atom'] == 'N':
                    if row['structure'] == 'helix' or row['structure'] == 'sheet':
                        # Add the positive coordinates to the positive coordinates list
                        positive_coordinates.append(
                            [row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'],
                             row['X'] + vector_row['X'], row['Y'] + vector_row['Y'], row['Z'] + vector_row['Z']])

                        # Add the negative coordinates to the negative coordinates list
                        negative_coordinates.append(
                            [row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'],
                             row['X'] - vector_row['X'], row['Y'] - vector_row['Y'], row['Z'] - vector_row['Z']])
                    else:
                        non_flanked_coordinates.append(
                            [row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'], row['X'],
                             row['Y'], row['Z']])
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

    # add the non-flanked coordinates to the final dataframe
    # final_df = pd.concat([final_df, non_flanked_df], ignore_index=True)

    # reorder the columns
    columns = ["atom_num", "atom", "residue", "resid", "chain", "X", "Y", "Z"]
    final_df = final_df[columns]

    return final_df


# Function that takes a dataframe of coordinates and a integer, "width", and returns a dataframe of vectors calculated as the vector between each dataframe row with "atom" value of "C" to the next row with matching "resid" and "atom" value of "O".
def DNA_vectors(df, width=1):
    # Filter the dataframe for rows with an 'atom' column value of "OP1" or "OP2"
    df = df[df['atom'].isin(['OP1', 'P'])]
    df = df.reset_index(drop=True)

    print(df.head())

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

    print(new_df.head())
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
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z", "structure"]

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        if df.loc[i, 'resid'] < df['resid'].max() - 1:
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
        # print("Rotated to X")
    if y_range < x_range and y_range < z_range:
        df = rotate_y(df)
        # print("Rotated to Y")
    if z_range < x_range and z_range < y_range:
        df = rotate_z(df)
        # print("Rotated to Z")

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
    #print("Number of points: ", point_len)

    # Perform B-spline interpolation
    tck, _ = splprep(points, s=smoothness)

    # Generate interpolated points
    u = np.linspace(0, 1, num=point_len)  # Increase num for more interpolated points
    interpolated_points = splev(u, tck)

    #print("Number of interpolated_ points: ", len(interpolated_points[0]))

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

    #print("interpolated dataframe: \n", interpolated_df.tail(n=10))
    #print("other dataframe: \n", other_df.tail(n=10))

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

    #print(interpolated_df.tail(n=10))

    return interpolated_df


def rotate_x(df):
    x = df['X']
    y = df['Y']
    z = df['Z']
    df['X'] = -z
    df['Y'] = x
    df['Z'] = y
    return df


def rotate_y(df):
    x = df['X']
    y = df['Y']
    z = df['Z']
    df['X'] = z
    df['Y'] = y
    df['Z'] = -x
    return df


def rotate_z(df):
    x = df['X']
    y = df['Y']
    z = df['Z']
    df['X'] = -y
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
    # print(rot_mats.head(n=10))
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


def unvectorize_df(df):
    # Initialize the X, Y, Z coordinates with the first row of the input dataframe
    x = [df.iloc[0]['dX']]
    y = [df.iloc[0]['dY']]
    z = [df.iloc[0]['dZ']]

    # Loop through the remaining rows of the input dataframe
    for i in range(1, len(df)):
        # Subtract the previous row's values from the current row's values
        x.append(x[i - 1] + df.iloc[i]['dX'])
        y.append(y[i - 1] + df.iloc[i]['dY'])
        z.append(z[i - 1] + df.iloc[i]['dZ'])

    # Create a new dataframe with the unvectorized coordinates
    replot_df = pd.DataFrame({'X': x, 'Y': y, 'Z': z})

    return replot_df


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


def atom_subset(df, atoms, include=True):
    if include:
        subset = df[df['atom'].isin(atoms)]
    else:
        subset = df[~df['atom'].isin(atoms)]
    return subset.reset_index(drop=True)


def find_intermediate_points(replot_df, keep_columns=False, atoms=None):
    other_atoms_df = pd.DataFrame(columns=replot_df.columns)

    # If atoms was passed a value, filter the dataframe by the atoms saving the filtered-out atoms in other_atoms_df
    if atoms:
        other_atoms_df = atom_subset(replot_df, atoms, include=False)
        replot_df = atom_subset(replot_df, atoms, include=True)

    # Initialize the new dataframe
    columns = ['X', 'Y', 'Z']

    if keep_columns:
        other_columns = replot_df.columns.drop(columns)
        final_columns = replot_df.columns
    else:
        final_columns = columns

    # initialize a new dataframe, new_data, with columns = final_columns
    new_data = pd.DataFrame(columns=final_columns)

    # Iterate over each row of the input dataframe
    for i in range(1, len(replot_df)):
        # Get the current and previous points
        point1 = replot_df.iloc[i - 1][columns].values
        point2 = replot_df.iloc[i][columns].values
        if replot_df.iloc[i - 1]['chain'] == replot_df.iloc[i]['chain']:
            # Use Bresenham's line algorithm to find the intermediate points
            intermediate_points = bresenham_line(*point1, *point2)
            # print(intermediate_points)

            # Convert to a small dataframe if intermediate_points is not empty
            if intermediate_points.size > 0:
                df_small = pd.DataFrame(intermediate_points, columns=columns)

                # Add the missing columns from replot_df.iloc[i] to df_small
                if keep_columns:
                    for col in other_columns:
                        df_small[col] = replot_df.iloc[i][col]
                # print(df_small)

                # Add the df_small dataframe to the new_data dataframe
                new_data = pd.concat([new_data, df_small], ignore_index=True)

            # Add the intermediate points to the new_data array
            # for p in intermediate_points:
            #    new_data.append(p)

    if len(other_atoms_df) > 0:
        new_data = pd.concat([new_data, other_atoms_df], ignore_index=True)

    return new_data
    # Create the new dataframe and return it


# return pd.DataFrame(new_data, columns=final_columns)

# Function that will take a pdb dataframe and a new dataframe and, starting at the first "atom" value of "O", will iteratively do the following:
# 1. Find the next "atom" value of "N" in the same "chain" value
# 2. Add that original "O" row to the new dataframe
# 3. Add a new row with identical column values except for an "atom" value of "Nz", and new X, Y, Z coordinates such that the distance between the "Nz" and the "N" are the same as the distance between the original "O" and the last "C" row. Also the new coordinates should be as close to the coordinates of "O"
# 4. Repeat steps 1-3 until the last "C" value in the "chain" is reached
# 5. Return the new dataframe

def add_nz(df):
    # Initialize the new dataframe
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z"]
    # Initialize a list to hold the new dataframe
    new_df = []

    # Variable to hold the direction between two points
    xyz = []
    # Variable to hold the distance between two points
    distance = 0

    # Iterate over each row until a row with an "atom" value of "C" is reached
    for i in range(len(df)):

        if df.iloc[i]['atom'] == 'C':
            # Check if the next row has an "atom" value of "O", but only if the next row is not the last row
            if df.iloc[i + 1]['atom'] == 'O' and i + 1 != len(df) - 1:

                # Calculate the direction between the "C" and "O" points
                xyz = df.iloc[i + 1][['X', 'Y', 'Z']].values - df.iloc[i][['X', 'Y', 'Z']].values
                # Calculate the distance between the "C" and "O" points
                distance = np.linalg.norm(xyz)
                # Add the "O" row to the new dataframe
                new_df.append(df.iloc[i + 1])

                # Iterate to find the next row with an "atom" value of "N", but only if the next row is not the last row:
                while df.iloc[i + 2]['atom'] != 'N' and i + 2 != len(df) - 1:
                    i += 1

                # Add a new "Nz" row to the new dataframe by copying the "N" row and changing the "atom" value to "Nz"
                new_df.append(df.iloc[i + 2])
                new_df[-1]['atom'] = 'Nz'
                # Calculate the new coordinates for the "Nz" row by using the same distance and direction but relative to the old "N" row and round to the nearest whole number
                new_df[-1][['X', 'Y', 'Z']] = df.iloc[i + 2][['X', 'Y', 'Z']].values + (
                            distance * xyz / np.linalg.norm(xyz))

                # Update the iterator to skip the already examined "N" and "O" rows, but only if the next row is not the last row
                if i + 6 <= len(df):
                    i += 2

    # Convert the float values in columns X, Y, and Z to integers
    for i in range(len(new_df)):
        new_df[i][['X', 'Y', 'Z']] = new_df[i][['X', 'Y', 'Z']].astype(int)

    test_df = pd.DataFrame(new_df, columns=columns)

    # Using the completed new_df, use the bresenham_line function to find the intermediate points between the "O" and "Nz" rows
    new_df = find_intermediate_points(pd.DataFrame(new_df, columns=columns))
    # Return the new dataframe
    return new_df


# Function that takes in a dataframe of coordinates and a raw PDB file
# Add a new column to the dataframe called "structure" and initialize all values to "None"
# Make a new dataframe called "structure_df" with columns "chain", "residue1", "resid1", "residue2", "resid2", and "structure"
# Search through the PDB file for rows starting with "HELIX", which will contain two "residue" and "resid" values per row and appear in columns 4-9. Add these values to the "structure_df" dataframe in addition to "helix" in structure column.
# Search through the PDB file for rows starting with "SHEET", which will contain four "residue" and "resid" values per row. The first two appear in columns 4-9. Add these values to the "structure_df" dataframe in addition to "sheet" in structure column.
# Next, from the same row "SHEET" row in the PDB file, the last two "residue" and "resid" values appear in columns 12-18. Add these values to the "structure_df" dataframe in addition to "sheet" in structure column.
# Now assume that in the structure_df, each row represents a range of residues that are part of a structure.
# Now for each row of the coordinate dataframe (df), check if the "chain", "residue", and "resid" values match any of the rows in the structure_df or if the "chain" matches and the "resid" is between "resid1" and "resid2".
# If there is a match, then change the "structure" value of the coordinate dataframe (df) to the value in the "structure" column of the structure_df.
# Return the coordinate dataframe (df)

def add_structure(df, pdb_file):
    # Add a structure column to the dataframe and initialize all values to "None"
    df['structure'] = "None"

    # Initialize the structure dataframe
    structure_df = pd.DataFrame(columns=['chain', 'residue1', 'resid1', 'residue2', 'resid2', 'structure'])

    # Open the PDB file
    with open(pdb_file, 'r') as f:
        # Iterate over each line in the PDB file searching for rows starting with "HELIX" or "SHEET"
        for line in f:
            if line.startswith("HELIX"):
                # Add the chain, residue, and resid values to the structure dataframe
                data = {'chain': line[19], 'residue1': line[15:19].strip(), 'resid1': line[22:26].strip(),
                        'residue2': line[27:31].strip(), 'resid2': line[34:38].strip(), 'structure': "helix"}
                structure_df = pd.concat([structure_df, pd.DataFrame(data, index=[0])], ignore_index=True)
            elif line.startswith("SHEET"):
                # Add the chain, residue, and resid values to the structure dataframe
                data1 = {'chain': line[21], 'residue1': line[17:21].strip(), 'resid1': line[22:27].strip(),
                         'residue2': line[28:32].strip(), 'resid2': line[34:38].strip(), 'structure': "sheet"}
                data2 = {'chain': line[49], 'residue1': line[44:48].strip(), 'resid1': line[52:55].strip(),
                         'residue2': line[59:63].strip(), 'resid2': line[67:70].strip(), 'structure': "sheet"}
                structure_df = pd.concat([structure_df, pd.DataFrame(data1, index=[0]), pd.DataFrame(data2, index=[0])],
                                         ignore_index=True)

    # Remove any rows with only space characters for columns 'chain', 'residue1', 'resid1', 'residue2', or 'resid2'
    structure_df = structure_df[structure_df['chain'].str.strip().astype(bool)]

    # print(structure_df.head(n=50))
    # Convert the 'str' values in the resid1 and resid2 columns to 'int'
    structure_df[['resid1', 'resid2']] = structure_df[['resid1', 'resid2']].astype(int)

    # Iterate over each row in the coordinate dataframe (df) and check if the "chain" and the "resid" value is between "resid1" and "resid2" in the structure dataframe. If so, add the structure value to the coordinate dataframe (df)
    for i, row in df.iterrows():
        # Find the matching row(s) in the structure dataframe
        matching_rows = structure_df[
            (structure_df['chain'] == row['chain']) & (structure_df['resid1'] <= row['resid']) & (
                        structure_df['resid2'] >= row['resid'])]
        # If there is a match, then change the "structure" value of the coordinate dataframe (df) to the value in the "structure" column of the structure_df.
        if len(matching_rows) > 0:
            df.at[i, 'structure'] = matching_rows['structure'].values[0]

    # Return the coordinate dataframe (df)
    return df


# Function that takes a dataframe of 3D coordinates and if four or more coordinates touch a location without any coordinates, then add a new coordinate at that location.
def add_missing_coordinates(df):
    # Get the column names of the dataframe
    columns = df.columns

    # Create a list for missing coordinates
    missing_coordinates = []

    # Iterate over each row in the coordinate dataframe (df)
    for i, row in df.iterrows():
        print(i)
        # check if the 8 neighboring locations have coordinates, and if not, save them to a list
        # Create a list of the 26 neighboring locations
        neighbors = [(row['X'] - 1, row['Y'] - 1, row['Z'] - 1),
                     (row['X'] - 1, row['Y'] - 1, row['Z']),
                     (row['X'] - 1, row['Y'] - 1, row['Z'] + 1),
                     (row['X'] - 1, row['Y'], row['Z'] - 1),
                     (row['X'] - 1, row['Y'], row['Z']),
                     (row['X'] - 1, row['Y'], row['Z'] + 1),
                     (row['X'] - 1, row['Y'] + 1, row['Z'] - 1),
                     (row['X'] - 1, row['Y'] + 1, row['Z']),
                     (row['X'] - 1, row['Y'] + 1, row['Z'] + 1),
                     (row['X'], row['Y'] - 1, row['Z'] - 1),
                     (row['X'], row['Y'] - 1, row['Z']),
                     (row['X'], row['Y'] - 1, row['Z'] + 1),
                     (row['X'], row['Y'], row['Z'] - 1),
                     (row['X'], row['Y'], row['Z'] + 1),
                     (row['X'], row['Y'] + 1, row['Z'] - 1), (row['X'], row['Y'] + 1, row['Z']),
                     (row['X'], row['Y'] + 1, row['Z'] + 1), (row['X'] + 1, row['Y'] - 1, row['Z'] - 1),
                     (row['X'] + 1, row['Y'] - 1, row['Z']), (row['X'] + 1, row['Y'] - 1, row['Z'] + 1),
                     (row['X'] + 1, row['Y'], row['Z'] - 1), (row['X'] + 1, row['Y'], row['Z']),
                     (row['X'] + 1, row['Y'], row['Z'] + 1), (row['X'] + 1, row['Y'] + 1, row['Z'] - 1),
                     (row['X'] + 1, row['Y'] + 1, row['Z']), (row['X'] + 1, row['Y'] + 1, row['Z'] + 1)]
        # Check if the 8 neighboring locations have coordinates, and if not, save them to a list
        for neighbor in neighbors:
            if not df[(df['X'] == neighbor[0]) & (df['Y'] == neighbor[1]) & (df['Z'] == neighbor[2])].empty:
                continue
            else:
                missing_coordinates.append(neighbor)

    # Create a new list for the missing coordinates with > 4 neighbors
    missing_coordinates_4 = []

    # For each missing coordinate, check if there are at least four other coordinates that touch that location, and if so, add a new coordinate at that location to a dataframe
    for missing_coordinate in missing_coordinates:
        # Create a list of the 26 neighboring locations
        neighbors = [(missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2]),
                     (missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2] + 1),
                     (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2] - 1),
                     (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2]),
                     (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2] + 1),
                     (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2]),
                     (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2] + 1),
                     (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2]),
                     (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2] + 1),
                     (missing_coordinate[0], missing_coordinate[1], missing_coordinate[2] - 1),
                     (missing_coordinate[0], missing_coordinate[1], missing_coordinate[2] + 1),
                     (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2]),
                     (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2] + 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2]),
                     (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2] + 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2] - 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2]),
                     (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2] + 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2] - 1),
                     (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2]),
                     (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2] + 1)]
        # Check if at least four of the neighbors exist in the dataframe
        count = 0
        for neighbor in neighbors:
            if not df[(df['X'] == neighbor[0]) & (df['Y'] == neighbor[1]) & (df['Z'] == neighbor[2])].empty:
                count += 1
        if count >= 4:
            missing_coordinates_4.append(missing_coordinate)

    # Add the missing_coordinates_4 to the dataframe, copying the values from the closest existing coordinate except for the 'X', 'Y', and 'Z' columns
    for missing_coordinate in missing_coordinates_4:
        # Find the dataframe row with the closest coordinates
        closest_coordinate = df.iloc[df.apply(lambda row: np.linalg.norm(
            np.array([row['X'], row['Y'], row['Z']]) - np.array(
                [missing_coordinate[0], missing_coordinate[1], missing_coordinate[2]])), axis=1).idxmin()]

        # Create a new row with the missing coordinate and the values from the closest coordinate
        new_row = pd.DataFrame([[closest_coordinate['atom_num'], closest_coordinate['atom'],
                                 closest_coordinate['residue'], closest_coordinate['resid'],
                                 closest_coordinate['chain'], missing_coordinate['X'], missing_coordinate['Y'],
                                 missing_coordinate['Z']]], columns=df.columns)

        # Add the new row to the dataframe
        df = df.append(new_row, ignore_index=True)
    return df


# Function that takes a dataframe of coordinates, filters for rows with an 'atom' column value of "N", "CA", and "C", assumes these coordinates make a contiguous line, and smoothens that line by adding more coordinates in between the existing coordinates and adjusting the existing coordinates.
def smooth_line(df):
    # calculate a resolution value by looking at the average 3D distance between the first coordinate with 'atom' value of "N" and the first coordinate with 'atom' value of "CA"
    # Filter the dataframe for rows with an 'atom' column value of "N" and "CA"
    temp_df = df[df['atom'].isin(['N', 'CA'])]

    # print(temp_df.head(n=10))

    # Calculate the 3D distance between the first coordinate with 'atom' value of "N" and the first coordinate with 'atom' value of "CA"
    distance = np.linalg.norm(temp_df.iloc[0][['X', 'Y', 'Z']] - temp_df.iloc[1][['X', 'Y', 'Z']])
    # Calculate the resolution value by rounding the distance up to the next integer

    resolution = int(np.ceil(distance)) * 5

    # Filter the dataframe for rows with an 'atom' column value of "N", "CA", and "C"
    df = df[df['atom'].isin(['N', 'CA', 'C'])]
    # df = df[df['atom'].isin(['N', 'C'])]

    # print(df.head(n=10))

    # Sort the dataframe by the 'resid' column
    df = df.sort_values(by=['resid'])

    # Create an empty list to store the coordinates
    coordinates = []

    # Ensure that resolution is an integer:
    resolution = int(resolution)

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        # Add the x, y, and z coordinates to the list
        coordinates.append(
            [row['X'], row['Y'], row['Z'], row['resid'], row['residue'], row['chain'], row['atom'], row['atom_num'],
             row['structure']])

    # Create an empty list to store the new coordinates
    new_coordinates = []
    # print(range(resolution))

    # Iterate over the coordinates list
    for i in range(len(coordinates) - 1):
        # Add the current coordinate to the new coordinates list
        new_coordinates.append(coordinates[i])

        # print(type(i))
        # print(type(resolution))

        # Calculate the difference between the current coordinate and the next coordinate
        diff = [coordinates[i + 1][j] - coordinates[i][j] for j in range(3)]
        # print(diff)
        # Add the difference to the current coordinate and divide by 3 to get the step size
        step = [diff[j] / resolution for j in range(3)]

        # Iterate over the range 1 to resolution value
        for j in range(1, resolution):
            # Add the new coordinate to the new coordinates list
            new_coordinates.append([coordinates[i][k] + step[k] * j for k in range(3)])

            # Round the new coordinates to the nearest whole number
            # new_coordinates[-1] = [round(new_coordinates[-1][k]) for k in range(3)]

            # Add 'resid' value of the current row to the new entries in the new coordinates list
            new_coordinates[-1].append(df['resid'].values[i])

            # Add 'residue' value of the current row to the new coordinates list
            new_coordinates[-1].append(df['residue'].values[i])

            # Add 'chain' value of the current row to the new coordinates list
            new_coordinates[-1].append(df['chain'].values[i])

            # Add 'atom' value of the current row to the new coordinates list
            new_coordinates[-1].append(df['atom'].values[i])

            # Add 'atom_number' value of the current row to the new coordinates list
            new_coordinates[-1].append(df['atom_num'].values[i])

            # Add 'structure' value of the current row to the new coordinates list
            new_coordinates[-1].append(df['structure'].values[i])

            # print(new_coordinates[-1])

    # print(new_coordinates)

    # Add the last coordinate to the new coordinates list
    new_coordinates.append(coordinates[-1])

    # Convert new_coordinates to a dataframe
    new_df = pd.DataFrame(new_coordinates,
                          columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain', 'atom', 'atom_num', 'structure'])

    # Reorder the columns of new_df as atom_num, atom, residue, resid, chain, X, Y, Z
    new_df = new_df[['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z', 'structure']]

    # Return the new dataframe
    return new_df

def sidechain(atom_df):
    if getattr(sys, 'frozen', False):
        # The program is running as a compiled executable
        base_path = sys._MEIPASS
        chains_file_path = os.path.join(base_path, 'PDB2MC', 'chains.txt')
    else:
        chains_file_path = pkg_resources.resource_filename('PDB2MC', 'chains.txt')

    chains_df = pd.read_csv(chains_file_path, sep='\s+', header=None, names=['residue', 'atom', 'atom2'],
                            engine='python')
    #chains_df = pd.read_csv("chains.txt", sep='\s+', header=None, names=['residue', 'atom', 'atom2'], engine='python')

    # Create an empty list to store the coordinates
    coordinates = []

    # Keep track of the current chain number and its index in the chain_values list
    current_chain_num = 1
    chain_values = atom_df["chain"].unique()
    chain_idx_dict = {chain_value: idx for idx, chain_value in enumerate(chain_values)}

    # Iterate over the rows of the atom dataframe
    for i, row in atom_df.iterrows():
        # Find the matching row(s) in the chains dataframe
        matching_chains = chains_df[(chains_df['residue'] == row['residue']) & (chains_df['atom'] == row['atom'])]

        # Iterate over the matching chain rows
        for _, chain_row in matching_chains.iterrows():
            # Find the next row in the atom dataframe that matches the residue and atom2 values
            #print(row['residue'], row['resid'], row['chain'], chain_row['atom2'])
            next_row = atom_df[(atom_df['residue'] == row['residue']) & (atom_df['resid'] == row['resid']) & (
                    atom_df['chain'] == row['chain']) & (atom_df['atom'] == chain_row['atom2'])].iloc[0]

            # Call the bresenham_line function and append the coordinates to the list
            if not next_row.empty:
                temp_coord = bresenham_line(row['X'], row['Y'], row['Z'], next_row['X'], next_row['Y'],
                                            next_row['Z']).tolist()
                for sublist in temp_coord:
                    sublist.append(current_chain_num)
                coordinates += temp_coord

        # Update the current chain number
        chain_idx = chain_idx_dict[row['chain']]
        current_chain_num = (chain_idx % 10) + 1


    # Create a dataframe from the coordinates list and return it
    coord_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'atom'])
    coord_df = coord_df.drop_duplicates()
    return coord_df


# Function that takes a dataframe of the coordinates of hollow spheres, and another dataframe of coordinates, and removes any points from the second dataframe that are inside the spheres
def remove_inside_spheres(sphere_df, coord_df, diameter):
    # Create a list to store the coordinates
    coordinates = []
    radius = diameter / 2

    # Find the coordinates of the sphere with the given diameter, round to the nearest integer
    coord = rasterized_sphere(radius)
    center = sphere_center(radius)
    sphere_coords = add_sphere_coordinates(coord, center, sphere_df, mesh=False)

    # print(sphere_coords.head(n=25))

    # Iterate over the rows of the coordinate dataframe
    for j, row2 in coord_df.iterrows():
        # Check if the point is inside the sphere
        if not is_inside_sphere(row2['X'], row2['Y'], row2['Z'], sphere_coords):
            # If not, add it to the list of coordinates
            coordinates.append(row2)

    # Create a dataframe from the coordinates list and return it
    return pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])


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


def filter_3d_array_with_bool(num_array, bool_array):

    num_array_copy = num_array.copy()
    bool_array_copy = bool_array.copy()

    # Ensure both arrays have the same shape
    if num_array_copy.shape != bool_array_copy.shape:
        raise ValueError("Input arrays must have the same shape.")

    # Element-wise multiplication with bool_array
    filtered_array = num_array_copy * bool_array_copy

    #breakpoint()
    return filtered_array

##TODO make sure to fix this
def save_3d_tiff(numpy_array, output_path):
    saved_array = numpy_array.copy()

    #check if it is a boolean area, if so then convert false to 0, and true to 255
    if saved_array.dtype == bool:
        saved_array = saved_array.astype(np.uint8)
        saved_array[saved_array == 0] = 0
        saved_array[saved_array == 1] = 255
    else:
        # Check array for values >255, if they exist change the value to 255
        saved_array[saved_array > 255] = 255

    # Check for values <0, if they exist change the value to 0
    saved_array[saved_array < 0] = 0

    # Ensure the numpy_array contains only integers
    saved_array = saved_array.astype(np.uint8)

    # Create a TiffWriter and write the NumPy array to a 3D TIFF file
    with tiff.TiffWriter(output_path) as tif:
        for i in range(numpy_array.shape[0]):
            # Save each 2D slice as a TIFF image
            tif.write(numpy_array[i])




def preprocess_3d_array(arr_3d, fill_value=1e7, empty_value=1e6):
    tmp_array = arr_3d

    # Replace fill_value with 0 and empty_value with 255
    tmp_array[tmp_array == fill_value] = 0
    tmp_array[tmp_array == empty_value] = 255

    # Replace any remaining values with 100
    tmp_array[(tmp_array != 0) & (tmp_array != 255)] = 150

    # Cast the array to np.uint8
    tmp_array = tmp_array.astype(np.uint8)

    return tmp_array

def SASA_gaussian_surface(arr_3d, sigma = 1.1, fill = False):

    image_array = arr_3d.copy()

    # Reverse the array values: 0 is now 255, >=1 is now 0
    image_array = np.where(image_array >= 1, 0, 255)

    # increase the size of the array by 10 in each dimension
    image_array = np.pad(image_array, 30, mode='constant', constant_values=255)

    # Create empty arrays for the three lines
    outer_line = np.zeros_like(image_array, dtype=np.uint8)
    center_line = np.zeros_like(image_array, dtype=np.uint8)
    inner_line = np.zeros_like(image_array, dtype=np.uint8)
    eroded_line = np.zeros_like(image_array, dtype=np.uint8)

    selem = np.array([[0, 0, 1, 0, 0],
                            [0, 1, 1, 1, 0],
                            [1, 1, 1, 1, 1],
                            [0, 1, 1, 1, 0],
                            [0, 0, 1, 0, 0]], dtype=np.uint8)

    # Iterate through each dimension (0, 1, 2)
    for j in range(0, 3):

        # Swap the axes for the current dimension
        if j == 2:
            image_array = np.swapaxes(image_array, 0, 1)
            image_array = np.swapaxes(image_array, 0, 2)
            inner_line = np.swapaxes(inner_line, 0, 1)
            inner_line = np.swapaxes(inner_line, 0, 2)
            eroded_line = np.swapaxes(eroded_line, 0, 1)
            eroded_line = np.swapaxes(eroded_line, 0, 2)
        elif j == 1:
            image_array = np.swapaxes(image_array, 1, 0)
            image_array = np.swapaxes(image_array, 2, 1)
            inner_line = np.swapaxes(inner_line, 1, 0)
            inner_line = np.swapaxes(inner_line, 2, 1)
            eroded_line = np.swapaxes(eroded_line, 1, 0)
            eroded_line = np.swapaxes(eroded_line, 2, 1)

        # Iterate through each slice of the 3D image
        for z in range(image_array.shape[0]):
            # Process each 2D slice
            slice = image_array[z]

            # Ensure the slice contains only integers
            slice = slice.astype(np.uint8)

            # Perform morphological erosion to simulate the rolling circle
            eroded = cv2.erode(slice, selem)

            # Calculate the outline by subtracting the eroded image from the original image
            outline = slice - eroded

            # Calculate the center line by eroding the outline
            center = cv2.erode(outline, selem)

            # Calculate the inner line by subtracting the center line from the outline
            inner = outline - center

            # center = cv2.morphologyEx(slice, cv2.MORPH_TOPHAT, selem)

            # Accumulate the results in the respective 3D arrays
            inner_line[z] += inner
            eroded_line[z] += eroded

        if j == 2:
            image_array = np.swapaxes(image_array, 0, 2)
            image_array = np.swapaxes(image_array, 0, 1)
            inner_line = np.swapaxes(inner_line, 0, 2)
            inner_line = np.swapaxes(inner_line, 0, 1)
            eroded_line = np.swapaxes(eroded_line, 0, 2)
            eroded_line = np.swapaxes(eroded_line, 0, 1)
        elif j == 1:
            image_array = np.swapaxes(image_array, 2, 0)
            image_array = np.swapaxes(image_array, 1, 2)
            inner_line = np.swapaxes(inner_line, 2, 0)
            inner_line = np.swapaxes(inner_line, 1, 2)
            eroded_line = np.swapaxes(eroded_line, 2, 0)
            eroded_line = np.swapaxes(eroded_line, 1, 2)

    # Ensure the values are reversed (0 is 255, >=1 is 0)
    inner_line = np.where(inner_line >= 1, 255, 0)

    inner_smooth = blur_3d_array(inner_line, sigma=sigma)
    inner_smooth = contour_outline(inner_smooth, fill=fill)

    save_3d_tiff(inner_smooth, r'C:\Users\marku\Desktop\pdb_blurred_inner_line.tif')

    #expanded = array_to_voxel(inner_smooth, original_array=image_array, padding_size=30)

    #return expanded
    return inner_smooth

def blur_3d_array(arr_3d, sigma=1):
    # Create a copy of the array
    arr_3d_copy = arr_3d.copy()

    #Add a layer of 5 zeroes on all sides of the array
    #arr_3d_copy = np.pad(arr_3d_copy, 10, mode='constant', constant_values=0)

    # Create a Gaussian filter
    gaussian_filter = ndimage.gaussian_filter(arr_3d_copy, sigma=sigma)

    # Cast the array to np.uint8
    gaussian_filter = gaussian_filter.astype(np.uint8)

    # Save your 3D NumPy array as a 3D TIFF image
    output_path = r'C:\Users\marku\Desktop\pdb_blurred_original_array.tif'  # Path where you want to save the TIFF image
    save_3d_tiff(gaussian_filter, output_path)

    # Change the values of the array to 0 or 255
    gaussian_filter[gaussian_filter >= 1] = 255

    return gaussian_filter

#A function that takes can take one to two arrays. If one array is taken, makes a dataframe with X, Y, Z columns that are the coordinates of the entries (>=1) in the array. If two arrays are taken, then it compares query_array to original_array and assumes that query_array was made by extending original_array on all sides by an equal amount. It derives that amount and returns a dataframe with the coordinates of the value (>= 1) of query_array adjusted for the change in size.
def array_to_voxel(query_array, original_array=None, padding_size=10):
    # Make a copy of the query array
    query_array_copy = query_array.copy()

    # Test to see if the query_array is a boolean array
    if query_array_copy.dtype == bool:
        query_array_copy = query_array_copy.astype(np.uint8)
        query_array_copy[query_array_copy == 0] = 0
        query_array_copy[query_array_copy == 1] = 255
    else:
        query_array_copy[query_array_copy >= 1] = 255

    # Find the coordinates of cells with values >= 1 in the query_array
    nonzero_coords = np.argwhere(query_array_copy >= 1)

    if original_array is None:
        # Create a voxel dataframe of the coordinates and an 'atom' column
        voxel_df = pd.DataFrame(nonzero_coords, columns=['X', 'Y', 'Z'])
        voxel_df['atom'] = 1
    else:
        # Make a copy of the original array
        original_array_copy = original_array.copy()

        # Test to see if original_array is boolean
        if original_array_copy.dtype == bool:
            original_array_copy = original_array_copy.astype(np.uint8)
            original_array_copy[original_array_copy == 0] = 0
            original_array_copy[original_array_copy == 1] = 255
        else:
            original_array_copy[original_array_copy >= 1] = 255

        # Find the coordinates of cells with values >= 1 in the query_array
        coords = np.argwhere(query_array >= 1)

        # Modify the coordinates only if the original array is provided
        if coords.size > 0:
            coords -= padding_size

        # Create a voxel dataframe of the coordinates and an 'atom' column
        voxel_df = pd.DataFrame(coords, columns=['X', 'Y', 'Z'])
        voxel_df['atom'] = 1

    return voxel_df

#A function that takes four dataframes: original_bonds, moved_bonds, hetatm_bonds, hetatm. It compares the min and max X, Y, Z coordinates of original_bonds and moved_bonds and alters the coordinates of hetatm_bonds and hetatm accordingly. It returns the altered hetatm_bonds and hetatm dataframes.
def adjust_hetatm_coordinates(original_bonds, moved_bonds, hetatm_bonds, hetatm):
    # Find the minimum and maximum coordinates of the original_bonds dataframe
    min_x, min_y, min_z = original_bonds[['X', 'Y', 'Z']].min()
    max_x, max_y, max_z = original_bonds[['X', 'Y', 'Z']].max()

    # Find the minimum and maximum coordinates of the moved_bonds dataframe
    min_x2, min_y2, min_z2 = moved_bonds[['X', 'Y', 'Z']].min()
    max_x2, max_y2, max_z2 = moved_bonds[['X', 'Y', 'Z']].max()

    # Find the difference between the minimum and maximum coordinates of the original_bonds and moved_bonds dataframes
    diff_x = min_x2 - min_x
    diff_y = min_y2 - min_y
    diff_z = min_z2 - min_z

    # Add the difference to the coordinates of the hetatm_bonds dataframe
    hetatm_bonds['X'] += diff_x
    hetatm_bonds['Y'] += diff_y
    hetatm_bonds['Z'] += diff_z

    # Add the difference to the coordinates of the hetatm dataframe
    hetatm['X'] += diff_x
    hetatm['Y'] += diff_y
    hetatm['Z'] += diff_z

    return hetatm, hetatm_bonds

# def array_to_voxel(arr_3d, atom):
#     # Find the coordinates where arr_3d is True
#     nonzero_coords = np.array(np.where(arr_3d)).T
#
#     #subtract 10 from each coordinate
#     nonzero_coords = nonzero_coords - 10
#
#     #subtract 40 from the x coordinate
#     nonzero_coords[:, 0] = nonzero_coords[:, 0] - 40
#
#     #subtract 3 to the y coordinate
#     nonzero_coords[:, 1] = nonzero_coords[:, 1] - 3
#
#     #subtract 35 from the z coordinate
#     nonzero_coords[:, 2] = nonzero_coords[:, 2] - 35
#
#     #Create a voxel dataframe of the coordinates and an 'atom' column from the atom parameter
#     voxel_df = pd.DataFrame(nonzero_coords, columns=['X', 'Y', 'Z'])
#     voxel_df['atom'] = atom
#
#     return voxel_df

def contour_outline(voxel_array, smooth=False, smooth_factor=0.02, fill = False):

    # make an empty 3d array with the shape of image_array
    final_tif = np.zeros(voxel_array.shape, dtype=np.uint8)

    #Ensure the voxel_array contains only integers
    voxel_array = voxel_array.astype(np.uint8)

    #Convert all numbers >= 1 to 100 in the voxel_array
    voxel_array[voxel_array >= 1] = 255

    # Iterate through 0 to 2
    for j in range(0, 3):

        filled_list = []

        # Swap the axes for the current dimension
        if j == 2:
            voxel_array = np.swapaxes(voxel_array, 0, 1)
            voxel_array = np.swapaxes(voxel_array, 0, 2)
        elif j == 1:
            voxel_array = np.swapaxes(voxel_array, 1, 0)
            voxel_array = np.swapaxes(voxel_array, 2, 1)


        # Iterate through each slice of the 3D image_array
        for i in range(voxel_array.shape[0]):

            gray = voxel_array[i, :, :]

            # Threshold the image to create a binary image
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

            if smooth:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            else:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Create a blank image with the same dimensions as the original image
            filled_img = np.zeros(gray.shape[:2], dtype=np.uint8)
            external_contours = []
            # Iterate over the contours and their hierarchies
            for i, contour in enumerate(contours):
                if smooth and hierarchy[0][i][3] == -1:
                    epsilon = smooth_factor * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [approx], -1, 255, thickness=1)
                elif fill and hierarchy[0][i][3] == -1:
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    #epsilon = 0.01 * cv2.arcLength(contour, True)
                    #cv2.drawContours(filled_img, [contour], -1, 255, thickness=cv2.FILLED)
                    external_contours.append(contour)
                    #cv2.drawContours(filled_img, [contour], -1, 255, thickness=1)
                # Check if the contour has a parent
                elif hierarchy[0][i][3] == -1:
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [contour], -1, 255, thickness=1)

            if fill:
                cv2.drawContours(filled_img, external_contours, -1, 255, thickness=cv2.FILLED)
            # append filled_im to filled_list
            filled_list.append(filled_img)

        temp_tif = np.asarray(filled_list)

        # Ensure the final_tif contains only integers
        temp_tif = temp_tif.astype(np.uint8)
        temp_tif[temp_tif >= 1] = 1

        if j == 2:
            voxel_array = np.swapaxes(voxel_array, 0, 2)
            voxel_array = np.swapaxes(voxel_array, 0, 1)
            temp_tif = np.swapaxes(temp_tif, 0, 2)
            temp_tif = np.swapaxes(temp_tif, 0, 1)

        elif j == 1:
            voxel_array = np.swapaxes(voxel_array, 2, 0)
            voxel_array = np.swapaxes(voxel_array, 1, 2)
            temp_tif = np.swapaxes(temp_tif, 2, 0)
            temp_tif = np.swapaxes(temp_tif, 1, 2)

        # Use np.logical_or to combine the two arrays
        final_tif = np.logical_or(final_tif, temp_tif)

    return final_tif

def find_border_cells(arr_3d):
    #Make a copy of the array and make the values np.int32
    arr_3d_copy = arr_3d.copy()
    arr_3d_copy = arr_3d_copy.astype(np.int32)

    # Define a shape
    # kernel = np.array([[[0, 0, 0],
    #                     [0, 1, 0],
    #                     [0, 0, 0]],
    #                    [[0, 1, 0],
    #                     [1, 1, 1],
    #                     [0, 1, 0]],
    #                    [[0, 0, 0],
    #                     [0, 1, 0],
    #                     [0, 0, 0]]])

    # Define a 3D kernel for the convolution operation
    kernel = np.ones((3, 3, 3), dtype=np.int32)

    # Perform the convolution operation
    convolved = convolve(arr_3d_copy, kernel, mode='constant', cval=0)


    # Create a boolean mask for cells that are filled (255) and have at least one neighboring cell that is empty (0)
    border_mask = (arr_3d_copy == 255) & (convolved < 255 * 27)

    # Apply the mask to the original array
    border_cells = np.where(border_mask, arr_3d_copy, 0)

    return border_cells
def align_and_filter_dataframes(numpy_array, original_df):
    # Convert the numpy array to a dataframe with columns X, Y, Z
    numpy_df = pd.DataFrame(np.argwhere(numpy_array >= 1), columns=['X', 'Y', 'Z'])

    # Find the minimum coordinates in both dataframes
    min_coords_numpy = numpy_df[['X', 'Y', 'Z']].min()
    min_coords_original = original_df[['X', 'Y', 'Z']].min()

    # Calculate the differences between the minimum coordinates
    coord_diff = min_coords_original - min_coords_numpy

    # Apply the coordinate differences to the numpy_df
    aligned_numpy_df = numpy_df + coord_diff

    # Merge the original_df and aligned_numpy_df on the coordinates
    merged_df = pd.merge(original_df, aligned_numpy_df, on=['X', 'Y', 'Z'], how='inner')

    #convert aligned_numpy_df to a 3d numpy array with filled values = 255

    aligned_numpy_array = construct_surface_array(aligned_numpy_df)
    #set all values >= 1 to 255
    aligned_numpy_array[aligned_numpy_array >= 1] = 255
    save_3d_tiff(aligned_numpy_array, r'C:\Users\marku\Desktop\pdb_aligned_numpy_array.tif')

    #convert merged_df to a 3d numpy array with filled values = 255
    merged_numpy_array = construct_surface_array(merged_df)
    #set all values >= 1 to 255
    merged_numpy_array[merged_numpy_array >= 1] = 255
    save_3d_tiff(merged_numpy_array, r'C:\Users\marku\Desktop\pdb_merged_numpy_array.tif')

    #convert the original df to a 3d numpy array with filled values = 255
    original_numpy_array = construct_surface_array(original_df)
    #Set all values >= 1 to 255
    original_numpy_array[original_numpy_array >= 1] = 255
    save_3d_tiff(original_numpy_array, r'C:\Users\marku\Desktop\pdb_original_numpy_array.tif')

    print("numpy rows: ", len(numpy_df))
    print("aligned numpy rows: ", len(aligned_numpy_df))
    print("original rows: ", len(merged_df))

    return merged_df


#Function that takes a dataframe of coordinates and a 3d numpy array and returns a dataframe only with the rows that have coordinates that are inside the 3d numpy array
def filter_df_with_array(df, arr_3d):
    #check to make sure the array is 0 if empty, and 255 if filled by checking 0, 0, 0 first
    if arr_3d[0, 0, 0] == 0:
        arr_3d[arr_3d == 0] = 0
        arr_3d[arr_3d >= 1] = 1
    else:
        arr_3d[arr_3d >= 1] = 0
        arr_3d[arr_3d == 0] = 1

    # Create an empty list to store the coordinates
    coordinates = []
    print(arr_3d.shape)
    print(df.max())
    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        # Check if the coordinates are inside the array
        if arr_3d[row['X'], row['Y'], row['Z']] >= 1:
            # If so, add the coordinates and 'atom' column of df to the list
            coordinates.append([row['X'], row['Y'], row['Z'], row['atom']])

    # Create a dataframe from the coordinates list and return it
    return pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'atom'])

def contour_outline2(voxel_array, smooth=False, smooth_factor=0.02, fill = False):

    # make an empty 3d array with the shape of image_array
    final_tif = np.zeros(voxel_array.shape, dtype=np.uint8)

    #Ensure the voxel_array contains only integers
    voxel_array = voxel_array.astype(np.uint8)

    #Convert all numbers >= 1 to 100 in the voxel_array
    voxel_array[voxel_array >= 1] = 255

    # Iterate through 0 to 2
    for j in range(0, 3):

        filled_list = []
        voxel_array = np.swapaxes(voxel_array, j, 0)
        print(voxel_array.shape)

        # Iterate through each slice of the 3D image_array
        for i in range(voxel_array.shape[0]):

            gray = voxel_array[i, :, :]

            # Threshold the image to create a binary image
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

            if smooth:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            else:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Create a blank image with the same dimensions as the original image
            filled_img = np.zeros(gray.shape[:2], dtype=np.uint8)

            # Iterate over the contours and their hierarchies
            for i, contour in enumerate(contours):
                if smooth and hierarchy[0][i][3] == -1:
                    epsilon = smooth_factor * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [approx], -1, 255, thickness=1)
                elif fill and hierarchy[0][i][3] == -1:
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [contour], -1, 255, thickness=cv2.FILLED)
                # Check if the contour has a parent
                elif hierarchy[0][i][3] == -1:
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [contour], -1, 255, thickness=1)


            # append filled_im to filled_list
            filled_list.append(filled_img)

        temp_tif = np.asarray(filled_list)

        # Ensure the final_tif contains only integers
        temp_tif = temp_tif.astype(np.uint8)
        temp_tif[temp_tif >= 1] = 1

        if j == 2:
            temp_tif = np.swapaxes(temp_tif, 0, 2)
            temp_tif = np.swapaxes(temp_tif, 0, 1)
        else:
            temp_tif = np.swapaxes(temp_tif, j, 0)

        # Use np.logical_or to combine the two arrays
        final_tif = np.logical_or(final_tif, temp_tif)

    return final_tif


def construct_surface_array_by_type(df, include=['backbone', 'branches']):
    # Determine the minimum and maximum coordinates from the DataFrame
    min_x, min_y, min_z = df[['X', 'Y', 'Z']].min()
    max_x, max_y, max_z = df[['X', 'Y', 'Z']].max()

    # Calculate the dimensions for the 3D numpy array
    dim_x = max_x - min_x + 1
    dim_y = max_y - min_y + 1
    dim_z = max_z - min_z + 1

    # Create an empty 3D numpy array filled with zeros
    array_3d = np.zeros((dim_x, dim_y, dim_z), dtype=np.uint8)
    extra = np.zeros((dim_x, dim_y, dim_z), dtype=np.uint8)

    # Create an atom mapping dictionary
    atom_mapping = {atom: 555 for atom in include}
    atom_mapping.update({atom: 1 for atom in df['atom'].unique() if atom not in include})

    # Iterate over the DataFrame rows and fill the array based on 'atom' values
    for _, row in df.iterrows():
        x, y, z = row['X'] - min_x, row['Y'] - min_y, row['Z'] - min_z
        atom_value = atom_mapping.get(row['atom'], 1)  # Default to 1 if not in mapping

        # Check if 'atom' value is included and if the array cell is not already filled
        if atom_value == 555 and array_3d[x, y, z] == 0:
            array_3d[x, y, z] = atom_value
        else:
            extra[x, y, z] = atom_value


    # Change all values >= 1 to 255
    array_3d[array_3d >= 1] = 255
    extra[extra >= 1] = 255

    save_3d_tiff(array_3d, r'C:\Users\marku\Desktop\point_inside_function.tif')
    save_3d_tiff(extra, r'C:\Users\marku\Desktop\point_inside_function_extra.tif')
    # Create an output array with filled cells based on the 'include' parameter
    #output_array = np.where(np.isin(array_3d, [555]), 255, 0).astype(np.uint8)

    return array_3d



def contour_outlinetwo(voxel_array, smooth=False, smooth_factor=0.02):

    # make an empty 3d array with the shape of image_array
    final_tif = np.zeros(voxel_array.shape, dtype=np.uint8)

    #Ensure the voxel_array contains only integers
    voxel_array = voxel_array.astype(np.uint8)

    #Convert all numbers >= 1 to 100 in the voxel_array
    voxel_array[voxel_array >= 1] = 255

    # Iterate through 0 to 2
    for j in range(0, 3):

        filled_list = []

        # Swap the axes for the current dimension
        if j == 2:
            voxel_array = np.swapaxes(voxel_array, 0, 1)
            voxel_array = np.swapaxes(voxel_array, 0, 2)
            final_tif = np.swapaxes(final_tif, 0, 1)
            final_tif = np.swapaxes(final_tif, 0, 2)
        elif j == 1:
            voxel_array = np.swapaxes(voxel_array, 1, 0)
            voxel_array = np.swapaxes(voxel_array, 2, 1)
            final_tif = np.swapaxes(final_tif, 1, 0)
            final_tif = np.swapaxes(final_tif, 2, 1)

       #print("On cycle ", j, " the shape is: ", voxel_array.shape)

        # Iterate through each slice of the 3D image_array
        for i in range(voxel_array.shape[0]):

            gray = voxel_array[i, :, :]

            # Threshold the image to create a binary image
            ret, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY)

            if smooth:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            else:
                # Find the contours in the binary image
                contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            # Create a blank image with the same dimensions as the original image
            filled_img = np.zeros(gray.shape[:2], dtype=np.uint8)

            # Iterate over the contours and their hierarchies
            for i, contour in enumerate(contours):
                if smooth and hierarchy[0][i][3] == -1:
                    epsilon = smooth_factor * cv2.arcLength(contour, True)
                    approx = cv2.approxPolyDP(contour, epsilon, True)
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [approx], -1, 255, thickness=1)
                # Check if the contour has a parent
                elif hierarchy[0][i][3] == -1:
                    # If the contour doesn't have a parent, fill it with pixel value 255
                    cv2.drawContours(filled_img, [contour], -1, 255, cv2.FILLED)

            # append filled_im to filled_list
            filled_list.append(filled_img)

        temp_tif = np.asarray(filled_list)

        #print("temp_tif on cycle ", j, " is ", temp_tif.shape)

        # Ensure the final_tif contains only integers
        temp_tif = temp_tif.astype(np.uint8)
        temp_tif[temp_tif >= 1] = 1
        final_tif = np.logical_or(final_tif, temp_tif)

        # Swap the axes for the current dimension
        if j == 2:
            voxel_array = np.swapaxes(voxel_array, 0, 2)
            voxel_array = np.swapaxes(voxel_array, 0, 1)
            final_tif = np.swapaxes(final_tif, 0, 2)
            final_tif = np.swapaxes(final_tif, 0, 1)
        elif j == 1:
            voxel_array = np.swapaxes(voxel_array, 2, 0)
            voxel_array = np.swapaxes(voxel_array, 1, 2)
            final_tif = np.swapaxes(final_tif, 2, 0)
            final_tif = np.swapaxes(final_tif, 1, 2)


    return final_tif


def filter_dataframe_by_array(df, arr_3d):
    modified_arr_3d = arr_3d.copy()

    # Ensure arr_3d contains only integers
    modified_arr_3d = modified_arr_3d.astype(np.uint32)

    arr_1d = modified_arr_3d.ravel()
    arr_1d = arr_1d[arr_1d != 0]

    #Convert arr_1d to a list called valid_indices
    valid_indices = arr_1d.tolist()
    valid_indices= [x - 1 for x in valid_indices]

    # Filter the DataFrame using these values
    filtered_df = df[df.index.isin(valid_indices)]

    return filtered_df
def paint_bucket_fill2old(voxel_array, original_dataframe):
    def is_valid(coords):
        z, y, x = coords
        return 0 <= z < voxel_array.shape[0] and 0 <= y < voxel_array.shape[1] and 0 <= x < voxel_array.shape[2]

    def get_neighbors(coords):
        z, y, x = coords
        neighbors = [(z + 1, y, x), (z - 1, y, x), (z, y + 1, x), (z, y - 1, x), (z, y, x + 1), (z, y, x - 1)]
        return [n for n in neighbors if is_valid(n)]

    def fill(coords):
        stack = [coords]
        while stack:
            current_coords = stack.pop()
            voxel_array[current_coords] = 1  # You can use any value you like here
            for neighbor in get_neighbors(current_coords):
                if voxel_array[neighbor] == 0:
                    stack.append(neighbor)

    empty_cells = (voxel_array == 0)
    bordering_empty = np.zeros(voxel_array.shape, dtype=bool)
    found_rows = set()

    for z in range(voxel_array.shape[0]):
        for y in range(voxel_array.shape[1]):
            for x in range(voxel_array.shape[2]):
                if empty_cells[z, y, x]:
                    neighbors = get_neighbors((z, y, x))
                    for nz, ny, nx in neighbors:
                        if is_valid((nz, ny, nx)):
                            bordering_empty[nz, ny, nx] = True

    result = np.where((voxel_array >= 1) & bordering_empty, voxel_array, 0)
    result = result.astype(int)
    output_np = result
    output_np[output_np >= 1] = 255
    with tiff.TiffWriter(r'C:\Users\marku\Desktop\test.tiff') as tif:
        for i in range(output_np.shape[0]):
            tif.write(output_np[i])

    print("printed :P")

    # Create a new DataFrame with selected rows
    selected_rows = original_dataframe[original_dataframe.index.isin(found_rows)]

    return result

def paint_bucket_fill(arr_3d, row=1, col=1, fill_value=1e7, empty_value=1e6):
    for _ in range(3):
        arr_3d = np.moveaxis(arr_3d, source=0, destination=2)
        depth = arr_3d.shape[2]
        queue = [(row, col, d) for d in range(depth)]

        while queue:
            r, c, d = queue.pop(0)

            if r < 0 or r >= arr_3d.shape[0] or c < 0 or c >= arr_3d.shape[1] or arr_3d[r, c, d] != empty_value:
                continue

            arr_3d[r, c, d] = fill_value
            queue.append((r + 1, c, d))
            queue.append((r - 1, c, d))
            queue.append((r, c + 1, d))
            queue.append((r, c - 1, d))

    # array_path = "C:/Users/Duronio Lab/Desktop/large_array.tif"
    # tiff_array = preprocess_3d_array(arr_3d)
    # tiff.imwrite(array_path, tiff_array)

    return arr_3d
def filter_dataframe_by_fill_value(arr_3d, df, fill_value=1e7):
    filtered_indices = set()
    for _ in range(3):
        arr_3d = np.moveaxis(arr_3d, source=0, destination=2)
        #arr_3d = np.moveaxis(arr_3d, source=0, destination=1)

        for d in range(arr_3d.shape[2]):
            for r in range(arr_3d.shape[0]):
                for c in range(arr_3d.shape[1]):
                    if arr_3d[r, c, d] == fill_value:
                        if r > 0 and arr_3d[r - 1, c, d] != fill_value:
                            filtered_indices.add(int(arr_3d[r - 1, c, d]))
                        if r < arr_3d.shape[0] - 1 and arr_3d[r + 1, c, d] != fill_value:
                            filtered_indices.add(int(arr_3d[r + 1, c, d]))
                        if c > 0 and arr_3d[r, c - 1, d] != fill_value:
                            filtered_indices.add(int(arr_3d[r, c - 1, d]))
                        if c < arr_3d.shape[1] - 1 and arr_3d[r, c + 1, d] != fill_value:
                            filtered_indices.add(int(arr_3d[r, c + 1, d]))

    filtered_df = df[df.index.isin(filtered_indices)].drop_duplicates()
    return filtered_df


# def filter_dataframe_by_array_bad(array, dataframe):
#     unique_values = np.unique(array[array != 0])
#
#     # Create an array of boolean masks to filter the DataFrame
#     masks = [dataframe.index == value for value in unique_values]
#
#     # Concatenate the masks along the rows to get a single boolean mask
#     combined_mask = np.any(masks, axis=0)
#
#     # Use the combined mask to filter the DataFrame
#     filtered_df = dataframe[combined_mask]
#
#     return filtered_df

def find_outer_surface(surface_array):
    surface_mask = np.zeros_like(surface_array, dtype=bool)

    for z in range(surface_array.shape[2]):
        slice_2d = surface_array[:, :, z]
        slice_2d = np.ravel(slice_2d)
        convolved = np.convolve(slice_2d < 1e6, np.array([1, 1, 1]), mode='same')
        print(convolved)
        surface_mask[:, :, z] = (convolved > 0) & (convolved < 3)

    surface_array[surface_mask] = surface_array[surface_mask]
    surface_array[surface_array == 1e6] = np.nan  # Remove the large value
    return surface_array


def filter_dataframe(original_df, surface_array):
    filtered_indices = [index for index in np.ravel(surface_array) if isinstance(index, int)]
    filtered_df = original_df.loc[filtered_indices]

    return filtered_df


def is_inside_sphere(x, y, z, sphere_coords):
    # Iterate over the coordinates of the sphere
    for coord in sphere_coords:
        # Check if the point is inside the sphere
        if x == coord[0] and y == coord[1] and z == coord[2]:
            return True
    return False


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


def sphere_coordinates(center, radius, num_points):
    phi = np.linspace(0, np.pi, num_points)
    theta = np.linspace(0, 2 * np.pi, num_points)
    phi, theta = np.meshgrid(phi, theta)

    x = center[0] + radius * np.sin(phi) * np.cos(theta)
    y = center[1] + radius * np.sin(phi) * np.sin(theta)
    z = center[2] + radius * np.cos(phi)

    return x, y, z


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

    # print(sphere)

    return sphere


## Need to change to mesh_mode, so it can be mesh, shell, or filled.
def add_sphere_coordinates(sphere_array, center, df, mesh=False):
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    new_rows = []

    for row_index, row in df.iterrows():
        for i, j, k in sphere_coords:
            i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
            distance = math.sqrt(i_norm ** 2 + j_norm ** 2 + k_norm ** 2)
            if abs(distance - math.ceil(sphere_array.shape[0] / 2)) <= 1 and mesh == True:
                new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
            if abs(distance - math.ceil(sphere_array.shape[0] / 2)) <= 3 and mesh == False:
                new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
    sphere_df = pd.DataFrame(new_rows, columns=['X', 'Y', 'Z', 'atom'])
    return sphere_df


def add_filled_sphere_coordinates(sphere_array, center, df):
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    new_rows = []

    for row_index, row in df.iterrows():
        for i, j, k in sphere_coords:
            i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
            #distance = math.sqrt(i_norm ** 2 + j_norm ** 2 + k_norm ** 2)
            new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
    sphere_df = pd.DataFrame(new_rows, columns=['X', 'Y', 'Z', 'atom'])
    return sphere_df

def fill_sphere_coordinates(sphere_array, center, df):
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    new_rows = []

    for row_index, row in df.iterrows():
        for i, j, k in sphere_coords:
            i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
            distance = math.sqrt(i_norm ** 2 + j_norm ** 2 + k_norm ** 2)
            new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
    sphere_df = pd.DataFrame(new_rows, columns=['X', 'Y', 'Z', 'atom'])
    return sphere_df


def process_coordinates(df):
    # Create an empty "hidden" column
    df["hidden"] = False

    # Loop through each row in the dataframe
    for i, row in df.iterrows():
        # Extract the coordinates of the current row
        x, y, z = row["X"], row["Y"], row["Z"]

        # Create a boolean array indicating whether each of the 6 surrounding coordinates exists in the dataframe
        surrounding = ((df["X"] == x + 1) & (df["Y"] == y) & (df["Z"] == z)) | \
                      ((df["X"] == x - 1) & (df["Y"] == y) & (df["Z"] == z)) | \
                      ((df["X"] == x) & (df["Y"] == y + 1) & (df["Z"] == z)) | \
                      ((df["X"] == x) & (df["Y"] == y - 1) & (df["Z"] == z)) | \
                      ((df["X"] == x) & (df["Y"] == y) & (df["Z"] == z + 1)) | \
                      ((df["X"] == x) & (df["Y"] == y) & (df["Z"] == z - 1))

        # Count the number of surrounding coordinates that exist in the dataframe
        num_surrounding = np.sum(surrounding)

        # Set the "hidden" column to True if there are 6 surrounding coordinates, False otherwise
        df.at[i, "hidden"] = num_surrounding == 6

    # Remove any rows where "hidden" is True
    df = df[df["hidden"] == False]

    # Remove the "hidden" column
    df = df.drop("hidden", axis=1)

    return df


def residue_to_atoms(df):
    df['atom'] = df['residue']
    return df


def shorten_atom_names(df):
    def shorten_atom(atom):
        if atom.startswith('O') or atom.startswith('N') or atom.startswith('C') or atom.startswith('S'):
            return atom[0]
        else:
            return atom[0:2] if not atom[0:2].isdigit() else atom[0]

    for index, row in df.iterrows():
        if row['row'] == 'ATOM':
            df.at[index, 'atom'] = shorten_atom(row['atom'])
        elif row['row'] == 'HETATM':
            df.at[index, 'atom'] = shorten_atom(row['atom'])

    return df


def change_mode(config):
    if config["mode"] == "Backbone":
        print("Backbone")
        config["show_atoms"] = False
        config["sidechain"] = False
        config["backbone"] = True
    elif config["mode"] == "Skeleton":
        print("Skeleton")
        config["show_atoms"] = False
        config["sidechain"] = True
        config["backbone"] = True
    elif config["mode"] == "Space Filling":
        print("TODO")
    elif config["mode"] == "X-ray":
        print("X-ray")
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
        print("X-ray Backbone")
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


def process_hetatom(atom_df, pdb_file):
    # #Filter HETATM lines with "HOH" in the fourth column
    # atom_df = atom_df[~((atom_df['row'] == 'HETATM') & (atom_df['atom'] == 'HOH'))]

    # Step 1: Read CONECT lines from file
    conect_ids = []
    with open(pdb_file, 'r') as f:
        for line in f:
            # Check if the line starts with "CONECT"
            if line.startswith("CONECT"):
                # Save the part after "CONECT" in the 'start' variable
                start = line[6:]

                # Split the 'start' variable into values of 5 characters each
                values = [start[i:i + 5] for i in range(0, len(start), 5)]

                # Remove any strings with only spaces from the list
                values = [value for value in values if value.strip()]

                if values:
                    base_value = int(values[0].replace(" ", ""))

                    for val in values[1:]:
                        val = val.replace(" ", "")
                        conect_ids.append([base_value, int(val)])

    # Step 2: Create dataframe from conect_ids
    conect_ids_df = pd.DataFrame(conect_ids, columns=['atom_1', 'atom_2'])
    # Step 3: Filter dataframe based on atoms present in atom_df
    valid_atoms = set(atom_df['atom_num'].astype(int).values)

    conect_ids_df = conect_ids_df[conect_ids_df['atom_1'].isin(valid_atoms) & conect_ids_df['atom_2'].isin(valid_atoms)]

    # Step 4: Call bresenham_line for each row in the dataframe
    results_df = pd.DataFrame(columns=['X', 'Y', 'Z'])
    atom1_coords = []
    atom2_coords = []

    for index, row in conect_ids_df.iterrows():
        atom1_coords = atom_df[atom_df['atom_num'].astype('int64') == row['atom_1']][['X', 'Y', 'Z']].values[0]
        atom2_coords = atom_df[atom_df['atom_num'].astype('int64') == row['atom_2']][['X', 'Y', 'Z']].values[0]

        atom1_coords = atom1_coords.reshape(1, 3)
        atom1 = pd.DataFrame(atom1_coords, columns=['X', 'Y', 'Z'])

        atom2_coords = atom2_coords.reshape(1, 3)
        atom2 = pd.DataFrame(atom2_coords, columns=['X', 'Y', 'Z'])

        line_coords = bresenham_line(atom1['X'].values[0], atom1['Y'].values[0], atom1['Z'].values[0],
                                     atom2['X'].values[0], atom2['Y'].values[0], atom2['Z'].values[0])

        results_df = pd.concat([results_df, pd.DataFrame(line_coords, columns=['X', 'Y', 'Z'])], ignore_index=True)

    # Step 5: Remove duplicate rows from results_df
    results_df = results_df.drop_duplicates()

    return results_df
