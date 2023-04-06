# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import os
import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

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


# def read_pdb(filename):
#    atom_lines = []
#    with open(filename, 'r') as f:
#        for line in f:
#            if line.startswith('ATOM'):
#                atom_lines.append(line.strip().split())
#
#    pdb_df = pd.DataFrame(atom_lines, columns=['Record', 'Atom_num', 'Atom_name', 'Res_name', 'Chain_id', 'Res_num', 'X', 'Y', 'Z', 'Occupancy', 'Temp_factor', 'Element'])
#    return pdb_df
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


def calculate_vectors(pdb_df):
    coords = pdb_df[['X', 'Y', 'Z']].values.astype(float)
    diffs = np.diff(coords, axis=0)
    vectors = np.insert(diffs, 0, np.nan, axis=0)
    vector_df = pd.DataFrame(vectors, columns=['dX', 'dY', 'dZ'])
    vector_df.iloc[0] = [0, 0, 0]
    return vector_df


def scale_coordinates(vector_df, scalar):
    scaled_df = vector_df.multiply(scalar, axis='rows')
    return scaled_df


def round_df(df):
    df = df.round()
    df = df.astype(int)
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


def sphere_coordinates(center, radius, num_points):
    phi = np.linspace(0, np.pi, num_points)
    theta = np.linspace(0, 2 * np.pi, num_points)
    phi, theta = np.meshgrid(phi, theta)

    x = center[0] + radius * np.sin(phi) * np.cos(theta)
    y = center[1] + radius * np.sin(phi) * np.sin(theta)
    z = center[2] + radius * np.cos(phi)

    return x, y, z

def rasterized_sphere(center, radius, shape):
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

def add_sphere_coordinates(sphere_array, center, df):
    sphere_coords = np.transpose(np.nonzero(sphere_array))
    new_rows = []
    for i, j, k in sphere_coords:
        i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
        new_rows.append([df.iloc[0]['X'] + i_norm, df.iloc[0]['Y'] + j_norm, df.iloc[0]['Z'] + k_norm])
    new_df = pd.DataFrame(new_rows, columns=['X', 'Y', 'Z'])
    new_df = new_df.astype(int)
    for index, row in df.iloc[1:].iterrows():
        center = (row['X'], row['Y'], row['Z'])
        sphere_coords = np.transpose(np.nonzero(sphere_array))
        for i, j, k in sphere_coords:
            i_norm, j_norm, k_norm = i - center[0], j - center[1], k - center[2]
            new_rows.append([row['X'] + i_norm, row['Y'] + j_norm, row['Z'] + k_norm])
    return pd.DataFrame(new_rows, columns=['X', 'Y', 'Z'])


def plot_3d_coordinates(df, n=30):
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(df['X'][:n], df['Y'][:n], df['Z'][:n])
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    plt.show()

def plot_cube(df, n):
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection='3d')

    for i in range(n):
        x = df.iloc[i]['X']
        y = df.iloc[i]['Y']
        z = df.iloc[i]['Z']
        ax.add_collection3d(Poly3DCollection([[(x, y, z), (x + 1, y, z), (x + 1, y + 1, z), (x, y + 1, z)],
                                              [(x, y, z), (x, y + 1, z), (x, y + 1, z + 1), (x, y, z + 1)],
                                              [(x, y, z), (x, y, z + 1), (x + 1, y, z + 1), (x + 1, y, z)],
                                              [(x + 1, y, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x + 1, y, z + 1)],
                                              [(x, y + 1, z), (x + 1, y + 1, z), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)],
                                              [(x, y, z + 1), (x + 1, y, z + 1), (x + 1, y + 1, z + 1), (x, y + 1, z + 1)]
                                             ], alpha=0.1, facecolor='blue', edgecolor='black'))

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    ax.set_xlim([0, df['X'].max()+1])
    ax.set_ylim([0, df['Y'].max()+1])
    ax.set_zlim([0, df['Z'].max()+1])
    plt.show()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # file_path = choose_subdir("")
    pdb_df = read_pdb(choose_file())
    #print(f'{pdb_df}')

    vector_df = calculate_vectors(pdb_df)
    #print(f'{vector_df}')

    scalar = 6.0
    scaled = scale_coordinates(vector_df, scalar)
    #print(scaled.head(10))

    unvector_df = unvectorize_df(scaled)
    #print(unvector_df.head(10))

    rounded = round_df(unvector_df)
    #print(rounded.head(10))

    intermediate = find_intermediate_points(rounded)
    #print(f'{intermediate}')

    coord = rasterized_sphere((2, 2, 2), 1.5, (5, 5, 5))
    # print(f'{coord}')

    spheres = add_sphere_coordinates(coord, (2, 2, 2), rounded)
    print(f'{spheres}')

    combined = pd.concat([spheres.head(200), intermediate.head(20)])
    combined = combined.reset_index(drop=True)
    #print(f'{combined}')

    #plot_3d_coordinates(spheres)
    plot_3d_coordinates(intermediate, 5)
    #plot_cube(combined, 60)
# See PyCharm help at https://www.jetbrains.com/help/pycharm/
