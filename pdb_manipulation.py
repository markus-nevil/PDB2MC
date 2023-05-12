import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
import math
import re


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
            if line.startswith('ATOM') or line.startswith("HETATM"):
                record = {'row': line[0:6].strip(),
                          'atom_num': line[7:11].strip(),
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
    coords_df = vector_df.loc[:, ['X', 'Y', 'Z']]
    other_df = vector_df.loc[:, ~vector_df.columns.isin(['X', 'Y', 'Z'])]

    # atom_col = vector_df['atom']
    # vector_df = vector_df.drop('atom', axis=1)

    # perform the scalar multiplication on the remaining columns
    scaled_df = coords_df.multiply(scalar, axis='rows')

    # add the 'atom' column back in to the scaled dataframe
    #scaled_df['atom'] = atom_col

    scaled_df = pd.concat([other_df, scaled_df], axis=1, sort=False)
    return scaled_df



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
# def filter_type_atom(df, remove_type=None, remove_atom=None):
#     # Check if remove_type is provided and create a boolean mask to filter out rows that match the criteria
#     if remove_type is not None:
#         if isinstance(remove_type, str):
#             mask = df['row'] != remove_type
#         elif isinstance(remove_type, list):
#             mask = ~df['row'].isin(remove_type)
#         else:
#             raise ValueError("remove_type parameter must be a string or a list")
#     else:
#         mask = [True] * len(df)  # Keep all rows by default
#
#     # Check if remove_atom is provided and add it to the mask as another criterion
#     if remove_atom is not None:
#         if isinstance(remove_atom, str):
#             mask &= ~df['atom'].str.startswith(remove_atom)
#         elif isinstance(remove_atom, list):
#             remove_atoms = '|'.join(remove_atom)
#             mask &= ~df['atom'].str.contains(f"^{remove_atoms}")
#         else:
#             raise ValueError("remove_atom parameter must be a string or a list")
#
#     # Return the filtered dataframe
#     return df[mask]


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
        if replot_df.iloc[i - 1]['chain'] == replot_df.iloc[i]['chain']:
            # Use Bresenham's line algorithm to find the intermediate points
            intermediate_points = bresenham_line(*point1, *point2)
            # Add the intermediate points to the new dataframe
            for p in intermediate_points:
                new_data.append(p)
    # Create the new dataframe and return it
    return pd.DataFrame(new_data, columns=columns)



# def sidechain(atom_df):
#
#     chains_df = pd.read_csv("chains.txt", sep='\s+', header=None, names=['residue', 'atom', 'atom2'], engine='python')
#
#     # Create an empty list to store the coordinates
#     coordinates = []
#
#     # Iterate over the rows of the atom dataframe
#     for i, row in atom_df.iterrows():
#         # Find the matching row(s) in the chains dataframe
#         matching_chains = chains_df[(chains_df['residue'] == row['residue']) & (chains_df['atom'] == row['atom'])]
#         # Iterate over the matching chain rows
#         for _, chain_row in matching_chains.iterrows():
#
#             # Find the next row in the atom dataframe that matches the residue and atom2 values
#             next_row = atom_df[(atom_df['residue'] == row['residue']) & (atom_df['resid'] == row['resid']) & (atom_df['chain'] == row['chain']) & (atom_df['atom'] == chain_row['atom2'])].iloc[0]
#
#             # Call the bresenham_line function and append the coordinates to the list
#             if not next_row.empty:
#                 coordinates += bresenham_line(row['X'], row['Y'], row['Z'], next_row['X'], next_row['Y'], next_row['Z']).tolist()
#
#     # Create a dataframe from the coordinates list and return it
#     coord_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])
#     coord_df = coord_df.drop_duplicates()
#
#     return coord_df

def sidechain(atom_df):
    chains_df = pd.read_csv("chains.txt", sep='\s+', header=None, names=['residue', 'atom', 'atom2'], engine='python')

    # Create an empty list to store the coordinates
    coordinates = []

    # Keep track of the current chain number and its index in the chain_values list
    current_chain_num = 1
    chain_values = atom_df["chain"].unique()
    chain_idx_dict = {chain_value: idx for idx, chain_value in enumerate(chain_values)}

    print(chain_values)
    print(chain_idx_dict)

    # Iterate over the rows of the atom dataframe
    for i, row in atom_df.iterrows():
        # Find the matching row(s) in the chains dataframe
        matching_chains = chains_df[(chains_df['residue'] == row['residue']) & (chains_df['atom'] == row['atom'])]

        # Iterate over the matching chain rows
        for _, chain_row in matching_chains.iterrows():
            # Find the next row in the atom dataframe that matches the residue and atom2 values
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


    #print(coordinates)
    # Create a dataframe from the coordinates list and return it
    coord_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'atom'])
    coord_df = coord_df.drop_duplicates()

    print(coord_df)

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
    diameter = math.ceil(radius) * 2 | 1
    mid_point = diameter // 2
    center = (mid_point, mid_point, mid_point)
    return (center)


# def rasterized_sphere(center, radius, shape):
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
        #print(config)
    elif config["mode"] == "Max":
        print("TODO")
    elif config["mode"] == "Min":
        print("TODO")
    return config


# def process_hetatom(df):
#
#     # Filter HETATM lines with "HOH" in the fourth column
#     df = df[~((df['row'] == 'HETATM') & (df['atom'] == 'HOH'))]
#
#     print(df)
#     # Step 2: Create a dictionary for CONECT records
#     conect_dict = {}
#     for _, row in df.iterrows():
#         if row['row'].startswith('CONECT'):
#             key = int(row['col2'])
#             values = [int(x) for x in row['col3':] if str(x).isdigit()]
#             conect_dict[key] = values
#
#     # Step 3: Filter dictionary based on keys present in DataFrame
#     valid_keys = set(df['row'].astype(int).values)
#     conect_dict = {k: v for k, v in conect_dict.items() if k in valid_keys}
#
#     # Step 4: Call bresenham_line for each key-value pair in the dictionary
#     results_df = pd.DataFrame(columns=['X', 'Y', 'Z'])
#     for key, values in conect_dict.items():
#         key_coords = df[df['row'] == key][['X', 'Y', 'Z']].values[0]
#         for value in values:
#             value_coords = df[df['row'] == value][['X', 'Y', 'Z']].values[0]
#             line_coords = list(bresenham_line(int(key_coords[0]), int(key_coords[1]), int(key_coords[2]),
#                                          int(value_coords[0]), int(value_coords[1]), int(value_coords[2])))
#             results_df = results_df.append(pd.DataFrame(line_coords, columns=['X', 'Y', 'Z']), ignore_index=True)
#
#     # Step 5: Remove duplicate rows from results_df
#     results_df = results_df.drop_duplicates()
#
#     return results_df

def process_hetatom(atom_df, pdb_file):
    # #Filter HETATM lines with "HOH" in the fourth column
    # atom_df = atom_df[~((atom_df['row'] == 'HETATM') & (atom_df['atom'] == 'HOH'))]


    # Step 1: Read CONECT lines from file
    conect_ids = []
    with open(pdb_file, 'r') as f:
        for line in f:
            if line.startswith('CONECT'):
                cols = line.split()
                atom1 = int(cols[1])
                for atom2 in cols[2:]:
                    conect_ids.append([atom1, int(atom2)])

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

        atom1_coords = atom1_coords.reshape(1,3)
        atom1 = pd.DataFrame(atom1_coords, columns=['X', 'Y', 'Z'])

        atom2_coords = atom2_coords.reshape(1,3)
        atom2 = pd.DataFrame(atom2_coords, columns=['X', 'Y', 'Z'])

        line_coords = bresenham_line(atom1['X'].values[0], atom1['Y'].values[0], atom1['Z'].values[0], atom2['X'].values[0], atom2['Y'].values[0], atom2['Z'].values[0])
        #results_df = results_df.append(pd.DataFrame(line_coords, columns=['X', 'Y', 'Z']), ignore_index=True)
        print(line_coords)
        results_df = pd.concat([results_df, pd.DataFrame(line_coords, columns=['X', 'Y', 'Z'])], ignore_index=True)

    # Step 5: Remove duplicate rows from results_df
    results_df = results_df.drop_duplicates()

    return results_df