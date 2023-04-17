import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
import math

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

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
            if line.startswith('ATOM'):
                record = {'atom': line[12:16].strip(),
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
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('HEADER'):
                code = line.strip().split()[-1]
                return code
    return None


def clip_coords(dataframe):
    tmp_df = dataframe[['atom', 'X', 'Y', 'Z']].copy()
    tmp_df[['X', 'Y', 'Z']] = tmp_df[['X', 'Y', 'Z']].astype(float)
    return tmp_df

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
    atom_col = vector_df['atom']
    vector_df = vector_df.drop('atom', axis=1)

    # perform the scalar multiplication on the remaining columns
    scaled_df = vector_df.multiply(scalar, axis='rows')

    # add the 'atom' column back in to the scaled dataframe
    scaled_df['atom'] = atom_col
    return scaled_df

def round_df(df):
    # extract the 'atom' column and remove it temporarily
    atom_col = df['atom']
    coords_df = df.drop('atom', axis=1)

    df = coords_df.round()
    df = df.astype(int)

    df['atom'] = atom_col
    return df

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

def find_intermediate_points(replot_df):
    # Initialize the new dataframe
    columns = ['X', 'Y', 'Z']
    new_data = []
    # Iterate over each row of the input dataframe
    for i in range(1, len(replot_df)):
        # Get the current and previous points
        point1 = replot_df.iloc[i - 1][columns].values
        point2 = replot_df.iloc[i][columns].values
        # Use Bresenham's line algorithm to find the intermediate points
        intermediate_points = bresenham_line(*point1, *point2)
        # Add the intermediate points to the new dataframe
        for p in intermediate_points:
            new_data.append(p)
    # Create the new dataframe and return it
    return pd.DataFrame(new_data, columns=columns)

def sidechain(df):
    coordinates = []
    new_data = []
    columns = ['X', 'Y', 'Z']
    prev_atom_pos = None
    prev_atom_branch = False
    sidechain_bool = False
    # try:
    for i, row in df.iterrows():

        #Detect what level of a chain it is on.
        if row['atom'] == 'CA':
            prev_atom_pos = df.iloc[i]
            sidechain_bool = True
        elif len(row['atom']) == 1 and row['atom'][0] == 'C':
            prev_atom_pos = df.iloc[i]
            sidechain_bool = True
        elif len(row['atom']) == 1 and row['atom'][0] == 'O':
            prev_atom_pos = df.iloc[i-1]
            sidechain_bool = True
        elif len(row['atom']) == 2 and (row['atom'][1] in ['B', 'G', 'D', 'E', 'Z']):
            k = 1
            prev_atom_pos = df.iloc[i-1]
            while len(prev_atom_pos['atom']) < 2:
                prev_atom_pos = df.iloc[i - k]
                k += 1
            sidechain_bool = True
        elif len(row['atom']) == 3:
            prev_atom_pos = df.iloc[i-1]
            sidechain_bool = True
            prev_atom_branch = True
        elif row['atom'] == 'OH':
            k = 1
            prev_atom_pos = df.iloc[i-1]
            while prev_atom_pos['atom'] != 'CZ':
                prev_atom_pos = df.iloc[i - k]
                k += 1
        else:
            prev_atom_pos = None
            sidechain_bool = False
            prev_atom_branch = False

        #Perform bresenham on the proper two atoms
        if len(row['atom']) == 1 and row['atom'][0] == 'O':
            #print("problem?")
            point1 = prev_atom_pos[columns].values
            point2 = row[columns].values
            # Use Bresenham's line algorithm to find the intermediate points
            coordinates = bresenham_line(*point1, *point2)

            sidechain_bool = False
            prev_atom_branch = False
        elif len(row['atom']) == 2:
            if(prev_atom_branch == True):
                #print("A")
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values
                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = bresenham_line(*point1, *point2)

                prev_atom_pos = df.iloc[i-2]
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values

                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = np.concatenate([coordinates, bresenham_line(*point1, *point2)])
                prev_atom_branch = False
                sidechain_bool = False
            else:
                #print("C")
                k = 1
                #print(row)
                while len(prev_atom_pos['atom']) < 2:
                    prev_atom_pos = df.iloc[i-k]
                    k += 1
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values
                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = bresenham_line(*point1, *point2)

                sidechain_bool = False
                prev_atom_branch = False
        elif len(row['atom']) == 3:
            #print("branch time!")
            #print(row)
            if len(prev_atom_pos['atom']) == 2:
                #print("oy")
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values
                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = bresenham_line(*point1, *point2)
            elif row['atom'][2] == prev_atom_pos['atom'][2]:
                #print("D")
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values
                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = bresenham_line(*point1, *point2)
            else:
                prev_atom_pos = df.iloc[i-2]
                #print("E")
                point1 = prev_atom_pos[columns].values
                point2 = row[columns].values
                # Use Bresenham's line algorithm to find the intermediate points
                coordinates = bresenham_line(*point1, *point2)
                prev_atom_branch = True
                sidechain_bool = False
        else:
            continue

        # Add the intermediate points to the new dataframe
        for p in coordinates:
            new_data.append(p)


    coord_df = pd.DataFrame(new_data, columns=['X', 'Y', 'Z'])
    return coord_df

def branch_lines(df):
    # Create an empty list to store the coordinates
    coordinates = []

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        # Skip rows with atom values of 2 or less characters
        if len(row['atom']) <= 2:
            continue

        # Extract the atom identity, position, and branch (if any) from the atom column
        atom = row['atom']
        atom_id = atom[0]
        atom_pos = atom[1]
        atom_branch = atom[2] if len(atom) == 3 else None

        # Initialize variables to store the previous atom position and branch (if any)
        prev_atom_pos = None
        prev_atom_branch = None

        # Search back through the previous rows to find the most recent row that satisfies the assumptions above
        for j in range(i - 1, -1, -1):
            prev_row = df.iloc[j]
            prev_atom = prev_row['atom']
            prev_atom_id = prev_atom[0]
            prev_atom_pos = prev_atom[1]
            prev_atom_branch = prev_atom[2] if len(prev_atom) == 3 else None

            # Check if the previous atom is the correct atom to connect to
            if prev_atom_id == 'N' and atom_id == 'C' and prev_atom_pos == atom_pos:
                coordinates += bresenham_line(prev_row['x_coord'], prev_row['y_coord'], prev_row['z_coord'],
                                              row['x_coord'], row['y_coord'], row['z_coord']).tolist()
                break
            elif prev_atom_id == 'C' and atom_id == 'O' and prev_atom_pos == atom_pos:
                coordinates += bresenham_line(prev_row['x_coord'], prev_row['y_coord'], prev_row['z_coord'],
                                              row['x_coord'], row['y_coord'], row['z_coord']).tolist()
                break
            elif prev_atom_id == 'C' and atom_id == 'N' and prev_atom_pos == atom_pos:
                coordinates += bresenham_line(prev_row['x_coord'], prev_row['y_coord'], prev_row['z_coord'],
                                              row['x_coord'], row['y_coord'], row['z_coord']).tolist()
                break
            elif prev_atom_id == 'C' and atom_id == 'C' and prev_atom_pos == atom_pos:
                if atom_branch is not None and prev_atom_branch is not None and atom_branch != prev_atom_branch:
                    coordinates += bresenham_line(prev_row['x_coord'], prev_row['y_coord'], prev_row['z_coord'],
                                                  row['x_coord'], row['y_coord'], row['z_coord']).tolist()
                    break
    coord_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])
    return coord_df

def sphere_coordinates(center, radius, num_points):
    phi = np.linspace(0, np.pi, num_points)
    theta = np.linspace(0, 2 * np.pi, num_points)
    phi, theta = np.meshgrid(phi, theta)

    x = center[0] + radius * np.sin(phi) * np.cos(theta)
    y = center[1] + radius * np.sin(phi) * np.sin(theta)
    z = center[2] + radius * np.cos(phi)

    return x, y, z

def sphere_center(radius):
    diameter = math.ceil(radius)*2 | 1
    mid_point = diameter // 2
    center = (mid_point, mid_point, mid_point)
    return(center)

#def rasterized_sphere(center, radius, shape):
def rasterized_sphere(radius):
    diameter = math.ceil(radius)*2 | 1
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

# def add_sphere_coordinates(sphere_array, center, df):
#     sphere_coords = np.transpose(np.nonzero(sphere_array))
#     new_rows = []
#     for row_index, row in df.iterrows():
#         for i, j, k in sphere_coords:
#             i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
#             new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
#     sphere_df = pd.DataFrame(new_rows, columns=['X', 'Y', 'Z', 'atom'])
#     return sphere_df

def add_sphere_coordinates(sphere_array, center, df, mesh=False):
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    new_rows = []
    for row_index, row in df.iterrows():
        for i, j, k in sphere_coords:
            i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
            distance = math.sqrt(i_norm ** 2 + j_norm ** 2 + k_norm ** 2)
            if abs(distance - math.ceil(sphere_array.shape[0] / 2)) <= 1 and mesh == True:
                new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm, row['atom']])
            if abs(distance - math.ceil(sphere_array.shape[0] / 2)) <= 2 and mesh == False:
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
        print(surrounding)

        # Count the number of surrounding coordinates that exist in the dataframe
        num_surrounding = np.sum(surrounding)

        # Set the "hidden" column to True if there are 6 surrounding coordinates, False otherwise
        df.at[i, "hidden"] = num_surrounding == 6

    # Remove any rows where "hidden" is True
    df = df[df["hidden"] == False]

    # Remove the "hidden" column
    df = df.drop("hidden", axis=1)

    return df


def shorten_atom_names(df):
    df['atom'] = df['atom'].str[0]
    return df

#print(rasterized_sphere(3))
