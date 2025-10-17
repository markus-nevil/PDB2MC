import pandas as pd
import os
from PDB2MC import variables
from shutil import copy
from zipfile import ZipFile
import re
import shutil
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from nbt_structure_utils import NBTStructure, BlockData, Vector

def extract_remarks_from_pdb(pdb_file, pdb_name):
    pdb_title = ""
    book_title = pdb_name
    pdb_authors = ""
    pdb_molecule = ""
    newline = r"\\n"

    with open(pdb_file, 'r') as file:
        for line in file:
            if line.startswith("AUTHOR"):
                parts = line.split("AUTHOR ")
                if len(parts) > 1:
                    pdb_authors = parts[1].strip()

            if line.startswith("TITLE"):
                parts = line.split("TITLE ")
                if len(parts) > 1:
                    pdb_title = parts[1].strip()

            match = re.match(r"COMPND\s+\d+\s+MOLECULE:", line)
            if match:
                parts = line.split("MOLECULE: ")
                if len(parts) > 1:
                    pdb_molecule += parts[1].strip() + r"\\n"

    book = f"give @p written_book{{pages:['{{\"text\":\"Title: {pdb_title}{newline}{newline}Authors: {pdb_authors}{newline}{newline}Molecule(s): {pdb_molecule}\"}}'],title:{book_title},author:PDB2MC}}"
    return book

def create_minecraft_functions(df, name, air, dir, blocks, replace=False):
    block_dict = blocks
    block_type = 'air' if air else 'block'
    functions = []

    # Add a line to set a minecraft obsidian block at the origin and a line to set a minecraft sign at the origin
    functions.append(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
    name = name.lower()

    for index, row in df.iterrows():
        x, y, z = row['X'], row['Y'], row['Z']

        if 'atom' in df.columns:
            # Check if block_dict is a single minecraft block
            if isinstance(block_dict, str):
                block = block_dict
            else:
                if str(row['atom']).isdigit():
                    block = variables.chain_blocks.get(str(row['atom']), 'gray_concrete')
                #Check if the str in the 'atom' is a digit and 'b'
                elif str(row['atom']).endswith('b'):
                    block = variables.dark_skeleton_blocks.get(str(row['atom']), 'gray_concrete')
                else:
                    block = block_dict.get(row['atom'], 'pink_concrete')
        else:
            block = block_dict.get('backbone_atom', 'pink_concrete')

        if air:
            block = 'air'
        x += 40
        # y += 70
        z += 40
        if replace:
            function = f'setblock ~{x} ~{y} ~{z} minecraft:{block} replace\n'
        else:
            function = f'setblock ~{x} ~{y} ~{z} minecraft:{block} keep\n'
        functions.append(function)

    num_files = (len(functions) // 1000000) + 1
    for i in range(num_files):
        file_num = i + 1
        filename = f"z{name}_{file_num}_{block_type}.mcfunction"
        filepath = os.path.join(dir, filename)
        start = i * 1000000
        end = start + 1000000
        with open(filepath, 'w') as f:
            f.writelines(functions[start:end])


def delete_nbt_mcfunctions_from_dir(save_directory):
    parent_directory = os.path.dirname(save_directory)

    directories_to_check = construct_save_paths(parent_directory)

    # make an empty list to store paths to files that will be deleted
    files_to_delete = []

    for directory in directories_to_check:
        # Check if the directory exists before attempting to list its contents
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith(".mcfunction"):
                    with open(os.path.join(directory, filename), 'r') as f:
                        if "setblock" or "place" in f.read():
                            files_to_delete.append(os.path.join(directory, filename))
                if filename.endswith(".nbt"):
                    files_to_delete.append(os.path.join(directory, filename))

    for file in files_to_delete:
        os.remove(file)

def delete_pdb_nbt_files(pdb_name, mc_dir):
    """
    Deletes all .nbt files in the generated/mc/structures directory that start with the given PDB name.
    """
    nbt_dir = mc_dir.split(r"\datapacks/mcPDB/data/protein/functions")[0]
    nbt_dir = nbt_dir + "/generated/mc/structures/"
    lower_pdb_name = pdb_name.lower()

    if os.path.exists(nbt_dir):
        for filename in os.listdir(nbt_dir):
            if filename.startswith(lower_pdb_name) and filename.endswith(".nbt"):
                os.remove(os.path.join(nbt_dir, filename))

def delete_mcfunctions(directory, name):
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.startswith("build_" + name) and filename.endswith(".mcfunction"):
                os.remove(os.path.join(directory, filename))
            if filename.startswith(name) and filename.endswith(".mcfunction"):
                os.remove(os.path.join(directory, filename))
            if filename.startswith(name) and filename.endswith(".nbt"):
                os.remove(os.path.join(directory, filename))
    else:
        print(f"Directory {directory} does not exist.")


def delete_old_files(mc_dir, pdb_name):
    # Delete the old mcfunctions if they match the current one
    delete_mcfunctions(mc_dir, "z" + pdb_name.lower())
    delete_mcfunctions(mc_dir, "build_" + pdb_name.lower())
    delete_mcfunctions(mc_dir, "clear_" + pdb_name.lower())

    # In the parallel directory named "function", delete the old mcfunction
    base_dir = os.path.dirname(mc_dir)  # Get the directory containing the "functions" directory
    new_dir = os.path.join(base_dir, "function")  # Path for the new "function" directory
    new_dir = os.path.normpath(new_dir)
    delete_mcfunctions(new_dir, "z" + pdb_name.lower())
    delete_mcfunctions(new_dir, "build_" + pdb_name.lower())
    delete_mcfunctions(new_dir, "clear_" + pdb_name.lower())

    # Split the path into parts
    normalized_path = os.path.normpath(mc_dir)
    path_parts = normalized_path.split(os.sep)

    # Find the index of '.minecraft/saves' and get the next part as the dynamic directory name
    try:
        minecraft_saves_index = path_parts.index('saves')
        dynamic_dir_name = os.sep.join(path_parts[:minecraft_saves_index + 2])
    except ValueError:
        dynamic_dir_name = None  # or handle the error as needed
        print("Error: No 'saves' directory found in path")

    if dynamic_dir_name:
        nbt_dir = os.path.normpath(os.path.join(os.sep.join(path_parts[:minecraft_saves_index]), dynamic_dir_name,
                                                "generated/mc/structures"))
        delete_mcfunctions(nbt_dir, pdb_name.lower())
        delete_mcfunctions(nbt_dir, "delete_" + pdb_name.lower())


def construct_save_paths(source_dir):
    # Normalize the path to ensure consistent directory separators
    normalized_path = os.path.normpath(source_dir)

    # Split the path into components
    path_parts = normalized_path.split(os.sep)

    # Find the index of the first occurrence of "saves"
    try:
        saves_index = path_parts.index('saves')
    except ValueError:
        return None  # "saves" not found in the path

    # Construct the base directory path by joining the path components up to "saves" and appending the variable directory name
    base_dir = os.sep.join(path_parts[:saves_index + 2])  # +2 to include "saves" and the variable directory name

    # Construct the target paths by appending the fixed structures to the base directory path
    paths = [
        os.path.join(base_dir, "generated/mc/structures"),
        os.path.join(base_dir, "datapacks/mcPDB/data/protein/function"),
        os.path.join(base_dir, "datapacks/mcPDB/data/protein/functions")
    ]

    return paths


def find_mcfunctions(directory, name):
    file_list = []
    for filename in os.listdir(directory):
        if filename.startswith("z"+name) and filename.endswith(".mcfunction"):
            parts = filename.split("_")
            full = filename.split(".")
            if len(parts) > 1:
                file_list.append(full[0])
    df = pd.DataFrame({"group": file_list})
    return df


def find_nbt(directory, name):
    file_list = []
    if os.path.exists(directory):
        for filename in os.listdir(directory):
            if filename.startswith(name) and filename.endswith(".nbt"):
                parts = filename.split("_")
                full = filename.split(".")
                if len(parts) > 1:
                    file_list.append(full[0])
    else:
        print(f"Directory {directory} does not exist.")
    df = pd.DataFrame({"group": file_list})
    return df


def find_delete_nbt(directory, name):
    file_list = []
    for filename in os.listdir(directory):
        if filename.startswith("delete_" + name) and filename.endswith(".nbt"):
            parts = filename.split("_")
            full = filename.split(".")
            if len(parts) > 1:
                file_list.append(full[0])
    df = pd.DataFrame({"group": file_list})
    return df


# Function that will move the PDB2MC directory from within the program directory into the Minecraft save directory
def copy_blank_world(mc_dir):
    # Get the current directory of the program
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the path to the PDB2MC directory
    pdb2mc_zip = os.path.join(current_dir, 'PDB2MC.zip')

    copy(pdb2mc_zip, mc_dir)

    dst_file = os.path.join(mc_dir, 'PDB2MC.zip')

    # Unzip the file
    with ZipFile(dst_file, 'r') as zip_ref:
        zip_ref.extractall(mc_dir)


def check_permissions(directory):
    # Check read permissions
    if os.access(directory, os.R_OK):
        print(f"You have read permission for {directory}")
    else:
        print(f"You do not have read permission for {directory}")

    # Check write permissions
    if os.access(directory, os.W_OK):
        print(f"You have write permission for {directory}")
    else:
        print(f"You do not have write permission for {directory}")


def create_clear_function(mc_dir, pdb_name):
    # find all files in the directory that start with "z" + pdb_name and copy all the lines into a list
    functions = []
    pdb_name = pdb_name.lower()

    for filename in os.listdir(mc_dir):
        if filename.startswith("z" + pdb_name) and filename.endswith(".mcfunction"):
            with open(os.path.join(mc_dir, filename), 'r') as f:
                # skip any lines that start with setblock ~ ~-1 ~
                functions += [x for x in f.readlines() if not x.startswith("setblock ~ ~-1 ~")]

    for i in range(len(functions)):
        if 'minecraft' in functions[i]:
            functions[i] = functions[i].split('minecraft', 1)[0] + 'minecraft:air replace\n'

    # remove duplicate lines
    functions = list(dict.fromkeys(functions))

    # create a clear_{name}.mcfunction file with the commands
    with open(os.path.join(mc_dir, f"clear_{pdb_name}.mcfunction"), 'w') as f:
        f.writelines(functions)


def create_master_function(df, name, directory, pdb_file):
    name = name.lower()

    # sort df by the naming convention
    df = df.sort_values('group', key=lambda x: x.str.split('_').str[1])

    # create a list of commands to execute each mcfunction in order
    commands = [f'function protein:{x}' for x in df['group']]

    # Open the first file and take the fifth setblock command and save it to a variable.
    with open(os.path.join(directory, f"{df['group'][0]}.mcfunction"), 'r') as f:
        lines = f.readlines()
        first_block = lines[2].split(" ")[1:4]
    # create a make_{name}.mcfunction file with the commands
    with open(os.path.join(directory, f"build_{name}.mcfunction"), 'w') as f:
        f.write(f'gamerule maxCommandChainLength 1000000\n')
        #f.write(extract_remarks_from_pdb(pdb_file, name))
        f.write('\n')
        f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')

        for i in range(0, len(commands)):
            f.write(f'{commands[i]}\n')


def create_simple_function(name, directory):
    functions = []
    pdb_name = name.lower()

    for filename in os.listdir(directory):
        if filename.startswith("z" + pdb_name) and filename.endswith(".mcfunction"):
            with open(os.path.join(directory, filename), 'r') as f:
                #skip any lines that start with setblock ~ ~-1 ~
                functions += [x for x in f.readlines() if not x.startswith("setblock ~ ~-1 ~")]

    #remove duplicate lines
    functions = list(dict.fromkeys(functions))

    # Take the coordinates of the fifth line and save it to a variable, "first_block"
    first_block = functions[2].split(" ")[1:4]

    # create a make_{name}.mcfunction file with the commands
    with open(os.path.join(directory, f"build_{pdb_name}.mcfunction"), 'w') as f:
        f.write(f'gamerule maxCommandChainLength 1000000\n')
        #f.write(extract_remarks_from_pdb(pdb_file, name))
        f.write('\n')
        f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')
        f.write(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
        f.writelines(functions)
    # create_structure_from_mcfunction(pdb_name, directory, functions)


# function that reads a .mcfunction file and uses nbt-structure-utils to make a structure from the setblock lines
def create_structure_from_mcfunction(name, directory, functions):
    pdb_name = name.lower()
    nbtstructure = NBTStructure()

    directory = directory.split(r"\datapacks/mcPDB/data/protein/functions")[0]
    directory = directory + "/generated/mc/structures/"

    # iterate through each line in functions
    for line in functions:
        block_type = line.split(' ')[4]
        block_type = str(block_type.split(':')[1])
        x = int(line.split(' ')[1].split('~')[1])
        y = int(line.split(' ')[2].split('~')[1])
        z = int(line.split(' ')[3].split('~')[1])
        nbtstructure.set_block(Vector(x, y, z), BlockData(block_type))

    nbt_file = os.path.join(directory, f"{pdb_name}.nbt")
    nbt_file = nbt_file.replace("/", "\\")

    nbtstructure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)


def process_nbt_chunk(chunk, block_dict, air, dir, name, idx):
    nbtstructure = NBTStructure()
    coords = chunk[['X', 'Y', 'Z']].round().astype(int).values
    coords[:, 0] += 40
    coords[:, 2] += 40

    if 'atom' in chunk.columns:
        atoms = chunk['atom'].astype(str).values
        if isinstance(block_dict, str):
            block_types = np.full(len(chunk), block_dict)
        else:
            block_types = np.array([
                variables.chain_blocks.get(a, 'gray_concrete') if a.isdigit() else
                variables.dark_skeleton_blocks.get(a, 'gray_concrete') if a.endswith('b') else
                block_dict.get(a, 'pink_concrete')
                for a in atoms
            ])
    else:
        block_types = np.full(len(chunk), block_dict.get('backbone_atom', 'pink_concrete'))

    if air:
        block_types[:] = 'air'

    for (x, y, z), block in zip(coords, block_types):
        nbtstructure.set_block(Vector(x, y, z), BlockData(block))

    nbt_file = os.path.join(dir, f"{name.lower()}_part{idx}.nbt").replace("/", "\\")
    nbtstructure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)

def create_nbt(df, name, air, dir, blocks, num_threads=4):
    dir = dir.split("\datapacks/mcPDB/data/protein/functions")[0]
    dir = dir + "/generated/mc/structures/"
    block_dict = blocks

    chunks = np.array_split(df, num_threads)
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for idx, chunk in enumerate(chunks):
            executor.submit(process_nbt_chunk, chunk, block_dict, air, dir, name, idx)

def create_nbt_function(mcfiles, pdb_name, directory):
    lower_pdb_name = pdb_name.lower()

    # sort df by the naming convention
    mcfiles['group'] = mcfiles['group'].astype(str)
    mcfiles = mcfiles.sort_values('group', key=lambda x: x.str.split('_').str[1])

    sidechain_backbone = mcfiles[mcfiles['group'].str.contains("sidechain|backbone")]

    # Remove these rows from the original DataFrame
    mcfiles = mcfiles[~mcfiles['group'].str.contains("sidechain|backbone")]

    # Append the extracted rows to the end of the DataFrame
    mcfiles = pd.concat([mcfiles, sidechain_backbone], ignore_index=True)

    with open(os.path.join(directory, f"build_{lower_pdb_name}.mcfunction"), 'w') as f:
        #f.write(extract_remarks_from_pdb(pdb_file, lower_pdb_name))
        #f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')
        f.write(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
        f.write(f'say Loading... please wait. May take some time.\n')
        #f.write(f'place template mc:{lower_pdb_name}')
        for item in mcfiles['group']:
            f.write(f'place template mc:{item}\n')


def create_individual_nbt_functions(mcfiles, directory):
    mcfiles_list = mcfiles.values.flatten().tolist()
    for file in mcfiles_list:
        basename = os.path.splitext(file)[0]
        with open(os.path.join(directory, f"build_{basename}.mcfunction"), 'w') as f:
            f.write(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
            f.write(f'say Loading {basename}... please wait. May take some time.\n')
            f.write(f'place template mc:{file}\n')


# def create_nbt_delete(pdb_name, mc_dir):
#     nbt_dir = mc_dir.split("\datapacks/mcPDB/data/protein/functions")[0]
#     nbt_dir = nbt_dir + "/generated/mc/structures/"
#
#     lower_pdb_name = pdb_name.lower()
#
#     #Iterate through the directory and for each .nbt file that starts with lower_pdb_name, print the name
#     for filename in os.listdir(nbt_dir):
#         if filename.startswith(lower_pdb_name) and filename.endswith(".nbt"):
#             nbt_structure = NBTStructure(os.path.join(nbt_dir, filename))
#             for block in nbt_structure.blocks:
#                 nbt_structure.set_block(block, BlockData('air'))
#
#             nbt_file = os.path.join(nbt_dir, f"delete_{filename}")
#             nbt_file = nbt_file.replace("/", "\\")
#             nbt_structure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)

def process_nbt_file(nbt_dir, filename):
    nbt_structure = NBTStructure(os.path.join(nbt_dir, filename))
    for block in nbt_structure.blocks:
        nbt_structure.set_block(block, BlockData('air'))
    nbt_file = os.path.join(nbt_dir, f"delete_{filename}").replace("/", "\\")
    nbt_structure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)

def create_nbt_delete(pdb_name, mc_dir):
    nbt_dir = mc_dir.split("\\datapacks/mcPDB/data/protein/functions")[0]
    nbt_dir = nbt_dir + "/generated/mc/structures/"
    lower_pdb_name = pdb_name.lower()

    files = [
        filename for filename in os.listdir(nbt_dir)
        if filename.startswith(lower_pdb_name) and filename.endswith(".nbt")
    ]

    with ThreadPoolExecutor() as executor:
        for filename in files:
            executor.submit(process_nbt_file, nbt_dir, filename)

def create_nbt_delete_function(mcfiles, pdb_name, directory):
    lower_pdb_name = pdb_name.lower()

    # sort df by the naming convention
    mcfiles['group'] = mcfiles['group'].astype(str)
    mcfiles = mcfiles.sort_values('group', key=lambda x: x.str.split('_').str[1])

    with open(os.path.join(directory, f"clear_{lower_pdb_name}.mcfunction"), 'w') as f:
        f.write(f'say Removing... must be standing on original obsidian block.\n')
        for item in mcfiles['group']:
            f.write(f'place template mc:{item}\n')

def adjust_y_coords(directory, pdb_name, nbtFile=False):
    min_y = None
    files = []

    if not nbtFile:
        # Collect all relevant files and their Y values in one pass
        y_values = []
        for filename in os.listdir(directory):
            if pdb_name in filename and filename.endswith(".mcfunction"):
                files.append(filename)
                with open(os.path.join(directory, filename), 'r') as f:
                    for line in f:
                        if line.startswith("setblock ~ ~-1 ~ minecraft:obsidian replace"):
                            continue
                        if 'setblock' in line:
                            try:
                                y = int(float(line.split(' ')[2].split('~')[1]))
                                y_values.append(y)
                            except (IndexError, ValueError):
                                continue
        if y_values:
            min_y = min(y_values)
        else:
            return  # No Y values found, nothing to adjust

        # Adjust Y values in the files
        for filename in files:
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as f:
                lines = f.readlines()
            with open(file_path, 'w') as f:
                for line in lines:
                    if line.startswith("setblock ~ ~-1 ~ minecraft:obsidian replace") or 'setblock' not in line:
                        f.write(line)
                        continue
                    parts = line.split(' ')
                    try:
                        y = int(float(parts[2].split('~')[1]))
                        adjusted_y = y - min_y
                        parts[2] = f"~{adjusted_y}"
                        line = ' '.join(parts)
                    except (IndexError, ValueError):
                        pass
                    f.write(line)
    else:
        # NBT file handling
        normalized_path = os.path.normpath(directory)
        path_parts = normalized_path.split(os.sep)
        try:
            minecraft_saves_index = path_parts.index('saves')
            dynamic_dir_name = os.sep.join(path_parts[:minecraft_saves_index + 2])
        except ValueError:
            print("Error: No 'saves' directory found in path")
            return

        nbt_dir = os.path.normpath(os.path.join(os.sep.join(path_parts[:minecraft_saves_index]), dynamic_dir_name, "generated/mc/structures"))

        nbt_y_values = []
        for filename in os.listdir(nbt_dir):
            if pdb_name in filename and filename.endswith(".nbt"):
                files.append(filename)
                nbt_structure = NBTStructure(os.path.join(nbt_dir, filename))
                nbt_y_values.append(nbt_structure.get_min_coords().y)
        if nbt_y_values:
            min_y = min(nbt_y_values)
        else:
            return

        for filename in files:
            nbt_structure = NBTStructure(os.path.join(nbt_dir, filename))
            nbt_structure.translate(Vector(0, -min_y, 0))
            nbt_structure.get_nbt(pressurize=False, align_to_origin=False).write_file(
                filename=os.path.join(nbt_dir, filename))

def copy_directory_contents(src, dest):

    # Ensure the destination directory exists
    if not os.path.exists(dest):
        os.makedirs(dest)

    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            # Recursively copy a directory
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            # Copy a file
            shutil.copy2(s, d)

def finish_nbts(mc_dir, config_data, pdb_name):
    nbt_dir = mc_dir.split(r"\datapacks/mcPDB/data/protein/functions")[0]
    nbt_dir = nbt_dir + "/generated/mc/structures/"

    mcfiles = find_nbt(nbt_dir, pdb_name.lower())

    if config_data["simple"]:
        create_nbt_function(mcfiles, pdb_name, mc_dir)
    else:
        create_individual_nbt_functions(mcfiles, mc_dir)

    base_dir = os.path.dirname(mc_dir)  # Get the directory containing the "functions" directory
    new_dir = os.path.join(base_dir, "function")  # Path for the new "function" directory

    # Copy contents from "functions" to "function"
    copy_directory_contents(mc_dir, new_dir)

def finish_delete_nbts(mc_dir, pdb_name):
    nbt_dir = mc_dir.split(r"\datapacks/mcPDB/data/protein/functions")[0]
    nbt_dir = nbt_dir + "/generated/mc/structures/"

    mcfiles = find_delete_nbt(nbt_dir, pdb_name.lower())

    create_nbt_delete_function(mcfiles, pdb_name, mc_dir)

    base_dir = os.path.dirname(mc_dir)  # Get the directory containing the "functions" directory
    new_dir = os.path.join(base_dir, "function")  # Path for the new "function" directory

    # Copy contents from "functions" to "function"
    copy_directory_contents(mc_dir, new_dir)