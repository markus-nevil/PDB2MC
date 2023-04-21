# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import pandas as pd
import csv
from variables import *
import os
import PySimpleGUI as sg
import json
import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import ast

#####
#####
# Look at this example for conditional windows:

import PySimpleGUI as sg

# Define layout for the main window
layout = [
    [sg.Text("Check the box to show the menu:")],
    [sg.Checkbox("Show Menu", key="-SHOW_MENU-")],
    [sg.Button("Exit")]
]

# Create the main window
window = sg.Window("Conditional Menu Example", layout)

# Loop to handle events
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break

    # Check the state of the checkbox
    show_menu = values["-SHOW_MENU-"]

    # Define layout for the conditional menu
    menu_layout = [
        [sg.Text("This is the menu!")],
        [sg.Button("Menu Option 1")],
        [sg.Button("Menu Option 2")],
        [sg.Button("Menu Option 3")]
    ]

    # Create the conditional menu window
    menu_window = sg.Window("Conditional Menu", menu_layout, visible=show_menu)

    # Loop to handle events for the conditional menu
    while True:
        menu_event, menu_values = menu_window.read()
        if menu_event == sg.WIN_CLOSED:
            break

    menu_window.close()

window.close()


########
### question mark info

# Define layout for the main window
layout = [
    [sg.Text("Click or hover over the question mark for more info:")],
    [sg.Button("", image_filename="question_mark.png", key="-INFO-")],
    [sg.Button("Exit")]
]

# Create the main window
window = sg.Window("Conditional Menu Example", layout)

# Loop to handle events
while True:
    event, values = window.read()
    if event == sg.WIN_CLOSED or event == "Exit":
        break

    # Check if the info button was clicked
    if event == "-INFO-":
        # Define layout for the info window
        info_layout = [
            [sg.Text("Additional information:")],
            [sg.Text("This is some extra information that is shown when you click or hover over the question mark.")],
            [sg.Button("OK")]
        ]

        # Create the info window
        info_window = sg.Window("Info", info_layout)

        # Loop to handle events for the info window
        while True:
            info_event, info_values = info_window.read()
            if info_event == sg.WIN_CLOSED or info_event == "OK":
                break

        info_window.close()

window.close()








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


def calculate_backbone_vectors(pdb_df):
    """Calculate vectors for atoms in protein structure"""
    # Initialize empty vector array
    vectors = np.zeros((len(pdb_df), 3))

    # Calculate backbone vectors
    backbone_atoms = ['N', 'CA', 'C']
    backbone_df = pdb_df[pdb_df['atom'].isin(backbone_atoms)]
    prev_resid = None
    prev_ca_coord = None
    for i, row in backbone_df.iterrows():
        # Calculate vector relative to previous residue's CA atom
        if row['resid'] != prev_resid:
            vectors[i] = row[['x', 'y', 'z']].values
            prev_resid = row['resid']
            prev_ca_coord = row[row['atom'] == 'CA'][['x', 'y', 'z']].values
        else:
            vectors[i] = row[['x', 'y', 'z']].values - prev_ca_coord
    return pd.DataFrame(vectors, columns=['dx', 'dy', 'z'])

# def calculate_vectors(pdb_df):
#     """Calculate vectors for atoms in protein structure"""
#     # Initialize empty vector array
#     vectors = np.zeros((len(pdb_df), 3))
#
#     # Calculate backbone vectors
#     backbone_atoms = ['N', 'CA', 'C']
#     backbone_df = pdb_df[pdb_df['atom'].isin(backbone_atoms)]
#     prev_resid = None
#     prev_ca_coord = None
#     for i, row in backbone_df.iterrows():
#         # Calculate vector relative to previous residue's CA atom
#         if row['resid'] != prev_resid:
#             vectors[i] = row[['x', 'y', 'z']].values
#             prev_resid = row['resid']
#             prev_ca_coord = row[row['atom'] == 'CA'][['x', 'y', 'z']].values
#         else:
#             vectors[i] = row[['x', 'y', 'z']].values - prev_ca_coord
#
#     # Calculate side chain vectors
#     current_resid = None
#     current_cb_coord = None
#     current_cg_coord = None
#     current_cd1_coord = None
#     current_cd2_coord = None
#     current_ce1_coord = None
#     current_ce2_coord = None
#     current_cz_coord = None
#
#     for i, row in pdb_df.iterrows():
#         # Determine if atom is in backbone or side chain
#         if row['atom'] in backbone_atoms:
#             continue
#         elif row['atom'] == 'CB':
#             # Calculate vector relative to CA atom in same residue
#             if row['resid'] == current_resid:
#                 vectors[i] = row[['x', 'y', 'z']].values - current_ca_coord
#                 current_cb_coord = row[['x', 'y', 'z']].values
#             else:
#                 current_resid = row['resid']
#                 current_ca_coord = pdb_df.loc[(pdb_df['resid'] == current_resid) & (pdb_df['atom'] == 'CA'),
#                                               ['x', 'y', 'z']].values
#                 vectors[i] = row[['x', 'y', 'z']].values - current_ca_coord
#                 current_cb_coord = row[['x', 'y', 'z']].values
#         elif row['atom'] == 'CG':
#             # Calculate vector relative to previous CB atom
#             vectors[i] = row[['x', 'y', 'z']].values - current_cb_coord
#             current_cg_coord = row[['x', 'y', 'z']].values
#         elif row['atom'].startswith('CD'):
#             if row['atom'] == 'CD1':
#                 # Calculate vector relative to previous CG atom
#                 vectors[i] = row[['x', 'y', 'z']].values - current_cg_coord
#                 current_cd1_coord = row[['x', 'y', 'z']].values
#             elif row['atom'] == 'CD2':
#                 # Calculate vector relative to previous CG atom
#                 vectors[i] = row[['x', 'y', 'z']].values - current_cg_coord
#                 current_cd2_coord = row[['x', 'y', 'z']].values
#         elif row['atom'].startswith('CE'):
#             if row['atom'] == 'CE1':
#                 # Calculate vector relative to previous CD1 atom
#                 vectors[i] = row[['x', 'y', 'z']].values - current_cd1_coord
#                 current_ce1_coord = row[['x', 'y', 'z']].values
#             elif row['atom'] == 'CE2':
#                 # Calculate vector relative to previous CD1 atom
#                 vectors[i] = row[['x', 'y', 'z']].values - current_cd2_coord
#                 current_ce2_coord = row[['x', 'y', 'z']].values
#
#
#
#
#     sidechain_df = pd.DataFrame(sidechain_vectors, columns=['dx', 'dy', 'dz'])
#     backbone_df = pd.DataFrame(backbone_vectors, columns=['dx', 'dy', 'dz'])
#     vector_df = pd.concat([sidechain_df, backbone_df])
#     return vector_df

def calculate_vectors_old(pdb_df):
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
    #pdb_df = read_pdb(choose_file())
    #print(f'{pdb_df}')

    # vector_df = calculate_vectors(pdb_df)
    # print(f'{vector_df}')

    #vector_df = calculate_backbone_vectors(pdb_df)

    #scalar = 3.0
    #scaled = scale_coordinates(vector_df, scalar)
    # #print(scaled.head(10))
    #
    #unvector_df = unvectorize_df(scaled)
    #print(unvector_df.head(10))
    #
    #rounded = round_df(unvector_df)
    # #print(rounded.head(10))
    #
    #intermediate = find_intermediate_points(rounded)
    # #print(f'{intermediate}')
    #
    # coord = rasterized_sphere((2, 2, 2), 1.5, (5, 5, 5))
    # # print(f'{coord}')
    #
    # spheres = add_sphere_coordinates(coord, (2, 2, 2), rounded)
    # print(f'{spheres}')
    #
    # combined = pd.concat([spheres.head(200), intermediate.head(20)])
    # combined = combined.reset_index(drop=True)
    # #print(f'{combined}')
    #
    # #plot_3d_coordinates(spheres)
    #plot_3d_coordinates(intermediate, 500)
    # #plot_cube(combined, 60)

    # # Load the list of decorative blocks
    # # Define the path to the text file containing the block RGB data
    # block_data_path = choose_file()
    #
    # # Create an empty list to store the RGB tuples
    # block_colors = []
    #
    # # Open the block data file and read in the data
    # with open(block_data_path, 'r') as block_data:
    #     block_data_reader = csv.reader(block_data, delimiter='\t')
    #     # Iterate over each row in the block data file
    #     for row in block_data_reader:
    #         # Check if the block name in the first column matches a decorative block
    #         if row[0] in decorative_blocks:
    #             # If it does, extract the RGB tuple from the third column
    #             rgb_tuple = tuple(map(int, row[2].split(',')))
    #             # Add the RGB tuple to the list of block colors
    #             block_colors.append(rgb_tuple)
    #
    # # Save the list of block colors as a .py file
    # with open('block_colors.py', 'w') as block_colors_file:
    #     block_colors_file.write(f"block_colors = {block_colors}")



    # rgb_tuples = []
    # block_data_path = choose_file()
    # with open(block_data_path, 'r') as f:
    #     for line in f:
    #         cols = line.strip().split('\t')
    #         block_name = cols[0].replace('.png', '')
    #         if block_name in decorative_blocks:
    #             rgb_tuple = ast.literal_eval(cols[2])
    #             rgb_tuples.append(rgb_tuple)
    #
    # with open('block_colors.py', 'w') as f:
    #     f.write(f"block_colors = {rgb_tuples}")
    #



    # Check if the config file exists
    if not os.path.isfile("config.json"):
        # If it doesn't exist, create it
        config = {
            "scale":1.0,
            "atoms": {
                "C": "black_concrete",
                "O": "red_concrete",
                "N": "blue_concrete",
                "S": "yellow_concrete",
                "backbone_atom": "gray_concrete",
                "sidechain_atom": "gray_concrete",
                "other_atom": "pink_concrete"
            },
            "mode": "Default",
            "backbone": True,
            "sidechain": True,
            "pdb_file": "",
            "save_path": ""
        }
        with open("config.json", "w") as f:
            json.dump(config, f)



# Define the layout of the window
layout = [
    [sg.Text("Select C atom"), sg.DropDown(decorative_blocks, key="C", default_value="black_concrete")],
    [sg.Text("Select O atom"), sg.DropDown(decorative_blocks, key="O", default_value="red_concrete")],
    [sg.Text("Select N atom"), sg.DropDown(decorative_blocks, key="N", default_value="blue_concrete")],
    [sg.Text("Select S atom"), sg.DropDown(decorative_blocks, key="S", default_value="yellow_concrete")],
    [sg.Text("Select backbone atom"), sg.DropDown(decorative_blocks, key="backbone_atom", default_value="gray_concrete")],
    [sg.Text("Select side chain atom"), sg.DropDown(decorative_blocks, key="sidechain_atom", default_value="gray_concrete")],
    [sg.Text("Select other atom"), sg.DropDown(decorative_blocks, key="other_atom", default_value="pink_concrete")],
    [sg.Text("Select mode"), sg.DropDown(["Default", "Skeleton"], key="mode", default_value="Default")],
    [sg.Checkbox("Backbone", default=True, key="backbone"), sg.Checkbox("Sidechain", default=True, key="sidechain")],
    [sg.Text("Scale"), sg.InputText(default_text="1.0", key="scale")],
    [sg.Button("Select PDB file"), sg.Button("Select Minecraft Save")],
    [sg.Button("Calculate", bind_return_key=True)]
]

# Create the window
window = sg.Window("My Window", layout)

# Loop to keep the window open
while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED:
        break

    if event == "Select PDB file":
        pdb_file = sg.popup_get_file("Select PDB file")
        # Save the pdb_file path to config.json
        with open("config.json", "r+") as f:
            config = json.load(f)
            config["pdb_file"] = pdb_file
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()

    if event == "Select Minecraft Save":
        save_path = sg.popup_get_folder("Select Minecraft Save directory")
        # Save the save_path to config.json
        with open("config.json", "r+") as f:
            config = json.load(f)
            config["save_path"] = save_path
            f.seek(0)
            json.dump(config, f, indent=4)
            f.truncate()

    if event == "Calculate":
        # Execute further code here
        print("C:", values["C"])
        print("O:", values["O"])
        print("N:", values["N"])
        print("S:", values["S"])
        print("mode:", values["mode"])
        print("backbone:", values["backbone"])
        print("sidechain:", values["sidechain"])
        print("scale:", values["scale"])
        print("save path:", config["save_path"])
        print("pdb file:", config["pdb_file"])

# Close the window
window.close()

