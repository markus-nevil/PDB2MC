import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
import math
import re
from scipy.interpolate import splprep, splev

def choose_file():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    return file_path

#Function that takes a pdb file, reads the coordinates of a single chain, and determines whether the shortest edge of the bounding box is shorter than the parameter ymax
def check_model_size(file_path, world_max):
    pdb_df = read_pdb(file_path)
    chain = pdb_df.loc[pdb_df['chain'] == 'A']
    chain = clip_coords(chain)
    ymin = chain['Y'].min()
    ymax = chain['Y'].max()
    ydiff = ymax - ymin
    if ydiff < world_max:
        return True
    else:
        return False

#Function that takes a pdb file, reads the coordinates of a single chain, determines the shortest edge of the bounding box, and determines the muliplication required to make that >= ymax.
def check_max_size(file_path, world_max):
    pdb_df = read_pdb(file_path)
    chain = pdb_df.loc[pdb_df['chain'] == 'A']
    chain = clip_coords(chain)
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

#Function that takes a dataframe of coordinates, finds the minimum Y value, sets that to -60, and then subtracts that value from all Y values
def set_min_y(df):
    min_y = df['Y'].min()
    df['Y'] = df['Y'] - min_y
    return df

#Function that takes a dataframe of coordinates and a integer, "width", and returns a dataframe of vectors calculated as the vector between each dataframe row with "atom" value of "C" to the next row with matching "resid" and "atom" value of "O".
def CO_vectors(df, width=1):
    # Filter the dataframe for rows with an 'atom' column value of "C" or "O"
    df = df[df['atom'].isin(['C', 'O'])]
    df = df.reset_index(drop=True)

    #print(df.tail(n=10))

    # Create an empty list to store the coordinates
    coordinates = []

    # Ensure that width is an integer:
    #width = int(width)

    #print(df['atom'][2])
    #Iterate over the rows of the dataframe and calculate the vector between the coordinates of each 'C' and 'O' with matching 'resid' values
    for i, row in df.iterrows():
        #print(i)
        #Calculate the 3D vector of row i and row i+1
        if i < len(df) - 1:
            #print(row['atom'] == 'C')
            #print(df['atom'][i+1] == 'O')
            #print(row['resid'] == df['resid'].values[i+1])
            if row['atom'] == 'C' and df['atom'][i + 1] == 'O' and row['resid'] == df['resid'][i + 1]:
                coordinates.append([df['X'].values[i + 1] - row['X'], df['Y'].values[i + 1] - row['Y'], df['Z'].values[i + 1] - row['Z'], row['resid'], row['residue'], row['chain']])
                #print(row['resid'], i, len(df), sep=" ")

    #multiply the vector by the width
    coordinates = [[coordinates[i][j] * width for j in range(3)] + coordinates[i][3:] for i in range(len(coordinates))]

    # Create a new dataframe with the new coordinates
    new_df = pd.DataFrame(coordinates, columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain'])

    #print("Here's the dataframe of vectors:")
    #print(new_df.tail(n=10))
    return new_df

#Function that will take the coordinates from a dataframe, match them with the vectors of another dataframe by "resid" column, and make two dataframes of each coordinate transformed by either the positive or negative of the matched vector. Then call bresenham_line function to fill the gaps. combine all 3 dataframes and return them.
def flank_coordinates(df, vector_df):

    # Create an empty list to store the positive coordinates
    positive_coordinates = []

    #Create an empty list to store the negative coordinates
    negative_coordinates = []

    #Create an empty list to store the non-flanked coordinates
    non_flanked_coordinates = []

    vector_iter_count = 1
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z", "structure"]

    #Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        if df.loc[i, 'resid'] < df['resid'].max() - 1:
            #Find the matching row in the vector dataframe
            matching_vector = vector_df[vector_df['resid'] == row['resid']]

            #subset df by rows that match the current row's resid
            match_len = len(df[df['resid'] == row['resid']])

            #Find the next row in the vector dataframe
            next_vector = vector_df[vector_df['resid'] == row['resid'] + 1]

            if False:
                #Subtract the X, Y, and Z coordinates of the next vector from the matching vector
                step_size_X = (next_vector.iloc[0]['X'] - matching_vector.iloc[0]['X']) / match_len
                step_size_Y = (next_vector.iloc[0]['Y'] - matching_vector.iloc[0]['Y']) / match_len
                step_size_Z = (next_vector.iloc[0]['Z'] - matching_vector.iloc[0]['Z']) / match_len

                #print("Here's the step size vector:", step_size_X, step_size_Y, step_size_Z, sep=" ")
                step_df = pd.DataFrame({'X': [step_size_X],
                                        'Y': [step_size_Y],
                                        'Z': [step_size_Z]})

                #Create a new dataframe and for X, Y, and Z coordinates add the step size vector to the matching vector
                vector_row = pd.DataFrame(columns=['X', 'Y', 'Z'])
                vector_row.loc[0,'X'] = matching_vector.iloc[0]['X'] + step_df.iloc[0]['X']*vector_iter_count
                vector_row.loc[0, 'Y'] = matching_vector.iloc[0]['Y'] + step_df.iloc[0]['Y']*vector_iter_count
                vector_row.loc[0, 'Z'] = matching_vector.iloc[0]['Z'] + step_df.iloc[0]['Z']*vector_iter_count

            #Iterate over the matching vector rows
            for j, vector_row in matching_vector.iterrows():

                if row['atom'] == 'CA' or row['atom'] == 'C' or row['atom'] == 'N':
                    if row['structure'] == 'helix' or row['structure'] == 'sheet':
                        #Add the positive coordinates to the positive coordinates list
                        positive_coordinates.append([row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'], row['X'] + vector_row['X'], row['Y'] + vector_row['Y'], row['Z'] + vector_row['Z']])

                        #Add the negative coordinates to the negative coordinates list
                        negative_coordinates.append([row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'], row['X'] - vector_row['X'], row['Y'] - vector_row['Y'], row['Z'] - vector_row['Z']])
                    else:
                        non_flanked_coordinates.append([row['atom_num'], row['atom'], row['residue'], row['resid'], row['chain'], row['X'], row['Y'], row['Z']])
                else:
                    continue
            if vector_iter_count > match_len:
                vector_iter_count = 1
            else:
                vector_iter_count += 1

    #Create a new dataframe with the positive coordinates
    positive_df = pd.DataFrame(positive_coordinates, columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    #Create a new dataframe with the negative coordinates
    negative_df = pd.DataFrame(negative_coordinates, columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    #Create a new dataframe with the non-flanked coordinates
    non_flanked_df = pd.DataFrame(non_flanked_coordinates, columns=['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z'])

    #Ensure all the values in the X, Y, Z columns are integers
    positive_df['X'] = positive_df['X'].astype(int)
    positive_df['Y'] = positive_df['Y'].astype(int)
    positive_df['Z'] = positive_df['Z'].astype(int)

    negative_df['X'] = negative_df['X'].astype(int)
    negative_df['Y'] = negative_df['Y'].astype(int)
    negative_df['Z'] = negative_df['Z'].astype(int)

    non_flanked_df['X'] = non_flanked_df['X'].astype(int)
    non_flanked_df['Y'] = non_flanked_df['Y'].astype(int)
    non_flanked_df['Z'] = non_flanked_df['Z'].astype(int)

    #Round the coordinates to the nearest whole number
    positive_df = positive_df.round()
    negative_df = negative_df.round()
    non_flanked_df = non_flanked_df.round()

    #iterate through each dataframe and call the bresenham_line function to fill in the gaps between each coordinate, add the new coordinates to a new dataframe, and return the new dataframe
    for i, row in positive_df.iterrows():

        #assume that positive_df and negative_df have the same number of rows and order of rows

        new_coordinates = bresenham_line(negative_df['X'][i], negative_df['Y'][i], negative_df['Z'][i], row['X'], row['Y'], row['Z'])
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

    #add the non-flanked coordinates to the final dataframe
    #final_df = pd.concat([final_df, non_flanked_df], ignore_index=True)



    #reorder the columns
    columns = ["atom_num", "atom", "residue", "resid", "chain", "X", "Y", "Z"]
    final_df = final_df[columns]

    return final_df



#Function that takes a dataframe of coordinates and finds the max and min values for X, Y, and Z, then assumes that is a box, then rotates the coordinates such that the smallest dimension of the box is now the Y axis. Returns a dataframe of the transformed coordinates.
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
        #print("Rotated to X")
    if y_range < x_range and y_range < z_range:
        df = rotate_y(df)
        #print("Rotated to Y")
    if z_range < x_range and z_range < y_range:
        df = rotate_z(df)
        #print("Rotated to Z")
    return df

def interpolate_dataframe(df, smoothness):

    #Check if there is an 'atom' column in the dataframe
    if 'atom' in df.columns:
        #Test if there are more than just backbone atoms (CA, C, N) in the dataframe, if so, split the dataframe into two dataframes, one with just backbone atoms and one with all atoms
        if len(df['atom'].unique()) > 3:
            other_df = df[~df['atom'].isin(['CA', 'C', 'N'])]
            backbone_df = df[df['atom'].isin(['CA', 'C', 'N'])]
            #Reset row number
            backbone_df = backbone_df.reset_index(drop=True)
        else:
            backbone_df = df
    else:
        backbone_df = df
        #Create an empty other_df with columns that match df
        other_df = pd.DataFrame(columns=df.columns)

    #Only select columns 'X', 'Y', and 'Z'
    backbone_coord_df = backbone_df[['X', 'Y', 'Z']]

    #Make a dataframe of the values that are not in the 'X', 'Y', and 'Z' columns from backbone_df
    backbone_extra_columns_df = backbone_df.drop(columns=['X', 'Y', 'Z'])


    # Extract X, Y, Z coordinates
    points = backbone_coord_df[['X', 'Y', 'Z']].values.T

    #Check if the points are floats, if not convert them to floats
    if points.dtype != 'float64':
        points = points.astype(float)
        points = points + 0.01
    else:
        #Add a decimal to the points if they don't have one
        points = points + 0.01
    point_len = len(points[0])
    print("Number of points: ",point_len)

    # Perform B-spline interpolation
    tck, _ = splprep(points, s=smoothness)

    # Generate interpolated points
    u = np.linspace(0, 1, num=point_len)  # Increase num for more interpolated points
    interpolated_points = splev(u, tck)

    print("Number of interpolated_ points: ", len(interpolated_points[0]))

    # Create a new dataframe with interpolated points
    interpolated_df = pd.DataFrame(
        {'X': interpolated_points[0], 'Y': interpolated_points[1], 'Z': interpolated_points[2]}
    )
    #Round the coordinates to the nearest whole number
    interpolated_df = interpolated_df.round()

    # Add the remaining columns back to the interpolated dataframe
    interpolated_df = pd.concat([interpolated_df, backbone_extra_columns_df], axis=1)

    #Re-order the columns of interpolated_df to match the original dataframe, df
    interpolated_df = interpolated_df[df.columns]

    print("interpolated dataframe: \n",interpolated_df.tail(n=10))
    print("other dataframe: \n",other_df.tail(n=10))

    #Concatenate the interpolated_df with the other_df and order them by the resid then atom_num
    if 'atom' in df.columns:
        if len(df['atom'].unique()) > 3:
            interpolated_df = pd.concat([interpolated_df, other_df], axis=0)
            interpolated_df = interpolated_df.sort_values(by=['resid', 'atom_num'])
            interpolated_df = interpolated_df.reset_index(drop=True)
        else:
            interpolated_df = pd.concat([interpolated_df, other_df], axis=0)
    else:
        interpolated_df = pd.concat([interpolated_df, other_df], axis=0)

    print(interpolated_df.tail(n=10))

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
    #scaled_df['atom'] = atom_col

    scaled_df = pd.concat([other_df, scaled_df], axis=1, sort=False)
    return scaled_df

def increase_cylinder_diameter(df, diameter):
    # Convert DataFrame to numpy array
    coords = df[['X', 'Y', 'Z']].values

    print(coords)
    # Calculate the vector between each point and the next point
    vecs = np.diff(coords, axis=0)

    # Calculate the length of each vector
    lens = np.sqrt(np.sum(vecs**2, axis=1))

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
    rot_vecs = rot_vecs * s[:, np.newaxis] + np.cross(rot_vecs, vecs) * c[:, np.newaxis] + vecs * np.sum(rot_vecs * vecs, axis=1)[:, np.newaxis] * (1 - c[:, np.newaxis])

    # Create a matrix of rotation matrices
    rot_mats = np.zeros((len(vecs), 3, 3))
    rot_mats[:, 0] = vecs
    rot_mats[:, 1:] = rot_vecs[:, np.newaxis]

    # Create a meshgrid of points in a circle
    n_pts = int(np.ceil(diameter))
    r = np.linspace(-n_pts/2, n_pts/2, n_pts)
    xx, yy = np.meshgrid(r, r)
    mask = np.sqrt(xx**2 + yy**2) <= diameter/2
    xx = xx[mask]
    yy = yy[mask]
    zz = np.zeros_like(xx)

    # Transform the meshgrid by each rotation matrix
    transformed_points = []
    #print(rot_mats.head(n=10))
    for i, mat in enumerate(rot_mats):
        print(mat)
        xyz = np.vstack((xx, yy, zz))
        print(xyz)
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

    #If atoms was passed a value, filter the dataframe by the atoms saving the filtered-out atoms in other_atoms_df
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

    #initialize a new dataframe, new_data, with columns = final_columns
    new_data = pd.DataFrame(columns=final_columns)

    # Iterate over each row of the input dataframe
    for i in range(1, len(replot_df)):
        # Get the current and previous points
        point1 = replot_df.iloc[i - 1][columns].values
        point2 = replot_df.iloc[i][columns].values
        if replot_df.iloc[i - 1]['chain'] == replot_df.iloc[i]['chain']:
            # Use Bresenham's line algorithm to find the intermediate points
            intermediate_points = bresenham_line(*point1, *point2)
            #print(intermediate_points)

            #Convert to a small dataframe if intermediate_points is not empty
            if intermediate_points.size > 0:
                df_small = pd.DataFrame(intermediate_points, columns=columns)

                #Add the missing columns from replot_df.iloc[i] to df_small
                if keep_columns:
                    for col in other_columns:
                        df_small[col] = replot_df.iloc[i][col]
                #print(df_small)

                #Add the df_small dataframe to the new_data dataframe
                new_data = pd.concat([new_data, df_small], ignore_index=True)

            # Add the intermediate points to the new_data array
            #for p in intermediate_points:
            #    new_data.append(p)

    if len(other_atoms_df) > 0:
        new_data = pd.concat([new_data, other_atoms_df], ignore_index=True)

    return new_data
    # Create the new dataframe and return it
   #return pd.DataFrame(new_data, columns=final_columns)

#Function that will take a pdb dataframe and a new dataframe and, starting at the first "atom" value of "O", will iteratively do the following:
#1. Find the next "atom" value of "N" in the same "chain" value
#2. Add that original "O" row to the new dataframe
#3. Add a new row with identical column values except for an "atom" value of "Nz", and new X, Y, Z coordinates such that the distance between the "Nz" and the "N" are the same as the distance between the original "O" and the last "C" row. Also the new coordinates should be as close to the coordinates of "O"
#4. Repeat steps 1-3 until the last "C" value in the "chain" is reached
#5. Return the new dataframe

def add_nz(df):
    #Initialize the new dataframe
    columns = ["atom_num", "atom", "residue", "chain", "resid", "X", "Y", "Z"]
    #Initialize a list to hold the new dataframe
    new_df = []

    #Variable to hold the direction between two points
    xyz = []
    #Variable to hold the distance between two points
    distance = 0
    print(df.head(n=25))
    #Iterate over each row until a row with an "atom" value of "C" is reached
    for i in range(len(df)):

        if df.iloc[i]['atom'] == 'C':
            #Check if the next row has an "atom" value of "O", but only if the next row is not the last row
            if df.iloc[i+1]['atom'] == 'O' and i+1 != len(df)-1:

                #Calculate the direction between the "C" and "O" points
                xyz = df.iloc[i+1][['X', 'Y', 'Z']].values - df.iloc[i][['X', 'Y', 'Z']].values
                #Calculate the distance between the "C" and "O" points
                distance = np.linalg.norm(xyz)
                #Add the "O" row to the new dataframe
                new_df.append(df.iloc[i+1])

                #Iterate to find the next row with an "atom" value of "N", but only if the next row is not the last row:
                while df.iloc[i+2]['atom'] != 'N' and i+2 != len(df)-1:
                    i += 1

                #Add a new "Nz" row to the new dataframe by copying the "N" row and changing the "atom" value to "Nz"
                new_df.append(df.iloc[i+2])
                new_df[-1]['atom'] = 'Nz'
                #Calculate the new coordinates for the "Nz" row by using the same distance and direction but relative to the old "N" row and round to the nearest whole number
                new_df[-1][['X', 'Y', 'Z']] = df.iloc[i+2][['X', 'Y', 'Z']].values + (distance * xyz / np.linalg.norm(xyz))

                #Update the iterator to skip the already examined "N" and "O" rows, but only if the next row is not the last row
                if i+6 <= len(df):
                    i += 2

    #Convert the float values in columns X, Y, and Z to integers
    for i in range(len(new_df)):
        new_df[i][['X', 'Y', 'Z']] = new_df[i][['X', 'Y', 'Z']].astype(int)

    test_df = pd.DataFrame(new_df, columns=columns)
    print(test_df.head(n=50))

    #Using the completed new_df, use the bresenham_line function to find the intermediate points between the "O" and "Nz" rows
    new_df = find_intermediate_points(pd.DataFrame(new_df, columns=columns))
    #Return the new dataframe
    return new_df

#Function that takes in a dataframe of coordinates and a raw PDB file
#Add a new column to the dataframe called "structure" and initialize all values to "None"
#Make a new dataframe called "structure_df" with columns "chain", "residue1", "resid1", "residue2", "resid2", and "structure"
#Search through the PDB file for rows starting with "HELIX", which will contain two "residue" and "resid" values per row and appear in columns 4-9. Add these values to the "structure_df" dataframe in addition to "helix" in structure column.
#Search through the PDB file for rows starting with "SHEET", which will contain four "residue" and "resid" values per row. The first two appear in columns 4-9. Add these values to the "structure_df" dataframe in addition to "sheet" in structure column.
#Next, from the same row "SHEET" row in the PDB file, the last two "residue" and "resid" values appear in columns 12-18. Add these values to the "structure_df" dataframe in addition to "sheet" in structure column.
#Now assume that in the structure_df, each row represents a range of residues that are part of a structure.
#Now for each row of the coordinate dataframe (df), check if the "chain", "residue", and "resid" values match any of the rows in the structure_df or if the "chain" matches and the "resid" is between "resid1" and "resid2".
#If there is a match, then change the "structure" value of the coordinate dataframe (df) to the value in the "structure" column of the structure_df.
#Return the coordinate dataframe (df)

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

    #print(structure_df.head(n=50))
    # Convert the 'str' values in the resid1 and resid2 columns to 'int'
    structure_df[['resid1', 'resid2']] = structure_df[['resid1', 'resid2']].astype(int)

    # Iterate over each row in the coordinate dataframe (df) and check if the "chain" and the "resid" value is between "resid1" and "resid2" in the structure dataframe. If so, add the structure value to the coordinate dataframe (df)
    for i, row in df.iterrows():
        # Find the matching row(s) in the structure dataframe
        matching_rows = structure_df[(structure_df['chain'] == row['chain']) & (structure_df['resid1'] <= row['resid']) & (structure_df['resid2'] >= row['resid'])]
        # If there is a match, then change the "structure" value of the coordinate dataframe (df) to the value in the "structure" column of the structure_df.
        if len(matching_rows) > 0:
            df.at[i, 'structure'] = matching_rows['structure'].values[0]

    # Return the coordinate dataframe (df)
    return df

#Function that takes a dataframe of 3D coordinates and if four or more coordinates touch a location without any coordinates, then add a new coordinate at that location.
def add_missing_coordinates(df):

    #Get the column names of the dataframe
    columns = df.columns

    # Create a list for missing coordinates
    missing_coordinates = []


    # Iterate over each row in the coordinate dataframe (df)
    for i, row in df.iterrows():
        print(i)
        #check if the 8 neighboring locations have coordinates, and if not, save them to a list
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
    print("Done making missing coordinates!: ", len(missing_coordinates))
    #Create a new list for the missing coordinates with > 4 neighbors
    missing_coordinates_4 = []

    # For each missing coordinate, check if there are at least four other coordinates that touch that location, and if so, add a new coordinate at that location to a dataframe
    for missing_coordinate in missing_coordinates:
        # Create a list of the 26 neighboring locations
        neighbors = [(missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2] - 1), (missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2]),
                    (missing_coordinate[0] - 1, missing_coordinate[1] - 1, missing_coordinate[2] + 1), (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2] - 1),
                    (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2]), (missing_coordinate[0] - 1, missing_coordinate[1], missing_coordinate[2] + 1),
                    (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2] - 1), (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2]),
                    (missing_coordinate[0] - 1, missing_coordinate[1] + 1, missing_coordinate[2] + 1), (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2] - 1),
                    (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2]), (missing_coordinate[0], missing_coordinate[1] - 1, missing_coordinate[2] + 1),
                    (missing_coordinate[0], missing_coordinate[1], missing_coordinate[2] - 1), (missing_coordinate[0], missing_coordinate[1], missing_coordinate[2] + 1),
                    (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2] - 1), (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2]),
                    (missing_coordinate[0], missing_coordinate[1] + 1, missing_coordinate[2] + 1), (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2] - 1),
                    (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2]), (missing_coordinate[0] + 1, missing_coordinate[1] - 1, missing_coordinate[2] + 1),
                    (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2] - 1), (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2]),
                    (missing_coordinate[0] + 1, missing_coordinate[1], missing_coordinate[2] + 1), (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2] - 1),
                    (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2]), (missing_coordinate[0] + 1, missing_coordinate[1] + 1, missing_coordinate[2] + 1)]
        #Check if at least four of the neighbors exist in the dataframe
        count = 0
        for neighbor in neighbors:
            if not df[(df['X'] == neighbor[0]) & (df['Y'] == neighbor[1]) & (df['Z'] == neighbor[2])].empty:
               count += 1
        if count >= 4:
            missing_coordinates_4.append(missing_coordinate)

    print("Done making missing coordinates with 4 neighbors!: ", len(missing_coordinates_4))
    #Add the missing_coordinates_4 to the dataframe, copying the values from the closest existing coordinate except for the 'X', 'Y', and 'Z' columns
    for missing_coordinate in missing_coordinates_4:
        #Find the dataframe row with the closest coordinates
        closest_coordinate = df.iloc[df.apply(lambda row: np.linalg.norm(np.array([row['X'], row['Y'], row['Z']]) - np.array([missing_coordinate[0], missing_coordinate[1], missing_coordinate[2]])), axis=1).idxmin()]

        #Create a new row with the missing coordinate and the values from the closest coordinate
        new_row = pd.DataFrame([[closest_coordinate['atom_num'], closest_coordinate['atom'], closest_coordinate['residue'], closest_coordinate['resid'], closest_coordinate['chain'], missing_coordinate['X'], missing_coordinate['Y'], missing_coordinate['Z']]], columns=df.columns)

        #Add the new row to the dataframe
        df = df.append(new_row, ignore_index=True)
    return df

#Function that takes a dataframe of coordinates, filters for rows with an 'atom' column value of "N", "CA", and "C", assumes these coordinates make a contiguous line, and smoothens that line by adding more coordinates in between the existing coordinates and adjusting the existing coordinates.
def smooth_line(df):

    #calculate a resolution value by looking at the average 3D distance between the first coordinate with 'atom' value of "N" and the first coordinate with 'atom' value of "CA"
    # Filter the dataframe for rows with an 'atom' column value of "N" and "CA"
    temp_df = df[df['atom'].isin(['N', 'CA'])]

    #print(temp_df.head(n=10))

    # Calculate the 3D distance between the first coordinate with 'atom' value of "N" and the first coordinate with 'atom' value of "CA"
    distance = np.linalg.norm(temp_df.iloc[0][['X', 'Y', 'Z']] - temp_df.iloc[1][['X', 'Y', 'Z']])
    # Calculate the resolution value by rounding the distance up to the next integer

    resolution = int(np.ceil(distance))*5
    print(resolution)

    # Filter the dataframe for rows with an 'atom' column value of "N", "CA", and "C"
    df = df[df['atom'].isin(['N', 'CA', 'C'])]
    #df = df[df['atom'].isin(['N', 'C'])]

    #print(df.head(n=10))

    # Sort the dataframe by the 'resid' column
    df = df.sort_values(by=['resid'])

    # Create an empty list to store the coordinates
    coordinates = []

    # Ensure that resolution is an integer:
    resolution = int(resolution)

    # Iterate over the rows of the dataframe
    for i, row in df.iterrows():
        # Add the x, y, and z coordinates to the list
        coordinates.append([row['X'], row['Y'], row['Z'], row['resid'],row['residue'], row['chain'], row['atom'], row['atom_num'], row['structure']])

    # Create an empty list to store the new coordinates
    new_coordinates = []
    #print(range(resolution))

    # Iterate over the coordinates list
    for i in range(len(coordinates) - 1):
        # Add the current coordinate to the new coordinates list
        new_coordinates.append(coordinates[i])

        #print(type(i))
        #print(type(resolution))

        # Calculate the difference between the current coordinate and the next coordinate
        diff = [coordinates[i + 1][j] - coordinates[i][j] for j in range(3)]
        #print(diff)
        # Add the difference to the current coordinate and divide by 3 to get the step size
        step = [diff[j] / resolution for j in range(3)]


        # Iterate over the range 1 to resolution value
        for j in range(1, resolution):
            # Add the new coordinate to the new coordinates list
            new_coordinates.append([coordinates[i][k] + step[k] * j for k in range(3)])

            #Round the new coordinates to the nearest whole number
            #new_coordinates[-1] = [round(new_coordinates[-1][k]) for k in range(3)]

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

            #print(new_coordinates[-1])

    #print(new_coordinates)

    # Add the last coordinate to the new coordinates list
    new_coordinates.append(coordinates[-1])

    # Convert new_coordinates to a dataframe
    new_df = pd.DataFrame(new_coordinates, columns=['X', 'Y', 'Z', 'resid', 'residue', 'chain', 'atom', 'atom_num', 'structure'])

    # Reorder the columns of new_df as atom_num, atom, residue, resid, chain, X, Y, Z
    new_df = new_df[['atom_num', 'atom', 'residue', 'resid', 'chain', 'X', 'Y', 'Z', 'structure']]

    # Return the new dataframe
    return new_df

def sidechain(atom_df):
    chains_df = pd.read_csv("chains.txt", sep='\s+', header=None, names=['residue', 'atom', 'atom2'], engine='python')

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

#Function that takes a dataframe of the coordinates of hollow spheres, and another dataframe of coordinates, and removes any points from the second dataframe that are inside the spheres
def remove_inside_spheres(sphere_df, coord_df, diameter):
    # Create a list to store the coordinates
    coordinates = []
    radius = diameter / 2


    #Find the coordinates of the sphere with the given diameter, round to the nearest integer
    coord = rasterized_sphere(radius)
    center = sphere_center(radius)
    sphere_coords = add_sphere_coordinates(coord, center, sphere_df, mesh=False)

    #print(sphere_coords.head(n=25))

    # Iterate over the rows of the coordinate dataframe
    for j, row2 in coord_df.iterrows():
        # Check if the point is inside the sphere
        if not is_inside_sphere(row2['X'], row2['Y'], row2['Z'], sphere_coords):
            # If not, add it to the list of coordinates
            coordinates.append(row2)

    # Create a dataframe from the coordinates list and return it
    return pd.DataFrame(coordinates, columns=['X', 'Y', 'Z'])

def is_inside_sphere(x, y, z, sphere_coords):
    # Iterate over the coordinates of the sphere
    for coord in sphere_coords:
        # Check if the point is inside the sphere
        if x == coord[0] and y == coord[1] and z == coord[2]:
            return True
    return False

#Function that takes a dataframe of coordinates of points that represent straight lines and a diameter and returns a dataframe of coordinates of new lines that represent a cylinder with the given diameter
def cylinderize(df, diameter):

    radius = diameter/2
    # Create an empty list to store the coordinates
    coordinates = []

    #print(df.head(n=20))
    #add an extra column to the dataframe named 'atom' and set all values to 'C'
    df['atom'] = 'C'

    # Use the add_sphere_coordinates function to add the coordinates of a sphere to each point in the dataframe
    coord = rasterized_sphere(radius)
    center = sphere_center(radius)
    sphere_coords = add_sphere_coordinates(coord, center, df, mesh=False)

    #remove duplicates from the dataframe
    sphere_coords = sphere_coords.drop_duplicates()

    #remove the extra column named 'atom'
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

    #print(sphere)

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
            if abs(distance - math.ceil(sphere_array.shape[0] / 2)) <= 2 and mesh == False:
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