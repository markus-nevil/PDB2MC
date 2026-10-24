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

# Minecraft 1.21 renamed the world's generated/<namespace>/structures folder to structure (and the datapack
# functions folder to function). Every .nbt is written to all of these folders so models load in both
# old and new versions; the first entry is where files are generated, the others are mirrors.
STRUCTURE_DIRS = ("structures", "structure")
FUNCTION_DIRS = ("functions", "function")
STRUCTURE_NAMESPACE = "mc"


def world_dir(mc_dir):
    """
    The world save folder for a path inside it. mc_dir is normally the datapack functions folder,
    <world>/datapacks/mcPDB/data/protein/functions, which may mix '/' and '\\' separators.
    """
    parts = os.path.normpath(mc_dir).split(os.sep)
    if 'datapacks' in parts:
        idx = len(parts) - 1 - parts[::-1].index('datapacks')
        return os.sep.join(parts[:idx]) or os.sep
    if 'saves' in parts:
        idx = parts.index('saves')
        return os.sep.join(parts[:idx + 2])
    return os.path.normpath(mc_dir)


def structure_dirs(mc_dir, create=True):
    """All generated/mc/structure(s) folders of the world; the first one is the primary output folder."""
    dirs = [os.path.join(world_dir(mc_dir), "generated", STRUCTURE_NAMESPACE, d) for d in STRUCTURE_DIRS]
    if create:
        for d in dirs:
            os.makedirs(d, exist_ok=True)
    return dirs


def function_dirs(mc_dir):
    """Both datapack function folders (functions = pre-1.21, function = 1.21+)."""
    base = os.path.dirname(os.path.normpath(mc_dir))
    return [os.path.join(base, d) for d in FUNCTION_DIRS]


def _is_model_file(filename, name, extension, prefixes=("",)):
    """
    True if filename is <prefix><name>.<ext> or <prefix><name>_*.<ext>. Matching on the '_' separator
    keeps model '1abc' from picking up (or deleting) the files of model '1abcd'.
    """
    if not filename.endswith(extension):
        return False
    stem = filename[:-len(extension)]
    for prefix in prefixes:
        full = prefix + name
        if stem == full or stem.startswith(full + "_"):
            return True
    return False


def _mirror_files(paths, src_dir, dirs):
    """Copy the given files from src_dir into every other folder in dirs."""
    for d in dirs:
        if os.path.normcase(d) == os.path.normcase(src_dir):
            continue
        os.makedirs(d, exist_ok=True)
        for path in paths:
            shutil.copy2(path, os.path.join(d, os.path.basename(path)))


def _run_all(tasks, max_workers=None):
    """Run (fn, *args) tasks in a thread pool and re-raise the first failure instead of dropping it."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(fn, *args) for fn, *args in tasks]
    return [f.result() for f in futures]


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


def _block_for_atom(atom, block_dict):
    """Block for one 'atom' label: chain numbers, dark chain numbers ('3b'), else the atom/element colour."""
    if atom.isdigit():
        return variables.chain_blocks.get(atom, 'gray_concrete')
    if atom.endswith('b') and atom in variables.dark_skeleton_blocks:
        return variables.dark_skeleton_blocks[atom]
    # Unknown atoms/elements use the user's "other" colour when one is configured
    return block_dict.get(atom, block_dict.get('other_atom', 'pink_concrete'))


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
                block = _block_for_atom(str(row['atom']), block_dict)
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
    """Remove every PDB2MC structure and function file from a world (Tools > delete all models)."""
    parent_directory = os.path.dirname(save_directory)

    directories_to_check = construct_save_paths(parent_directory) or []

    # make an empty list to store paths to files that will be deleted
    files_to_delete = []

    for directory in directories_to_check:
        # Check if the directory exists before attempting to list its contents
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith(".mcfunction"):
                    with open(os.path.join(directory, filename), 'r') as f:
                        contents = f.read()
                    if "setblock" in contents or "place" in contents:
                        files_to_delete.append(os.path.join(directory, filename))
                if filename.endswith(".nbt"):
                    files_to_delete.append(os.path.join(directory, filename))

    for file in files_to_delete:
        os.remove(file)


def delete_pdb_nbt_files(pdb_name, mc_dir):
    """
    Deletes the .nbt files (including delete_ structures) of the given model from every structure folder.
    """
    lower_pdb_name = pdb_name.lower()
    for nbt_dir in structure_dirs(mc_dir, create=False):
        if os.path.exists(nbt_dir):
            for filename in os.listdir(nbt_dir):
                if _is_model_file(filename, lower_pdb_name, ".nbt", prefixes=("", "delete_")):
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
        print(f"Delete mcfunctions: Directory {directory} does not exist.")


def delete_old_files(mc_dir, pdb_name):
    """Remove all previously generated function and structure files of this model."""
    name = pdb_name.lower()
    for directory in function_dirs(mc_dir):
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if _is_model_file(filename, name, ".mcfunction", prefixes=("z", "build_", "clear_")):
                    os.remove(os.path.join(directory, filename))
    delete_pdb_nbt_files(name, mc_dir)


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
    paths = [os.path.join(base_dir, "generated", STRUCTURE_NAMESPACE, d) for d in STRUCTURE_DIRS]
    paths += [os.path.join(base_dir, "datapacks", "mcPDB", "data", "protein", d) for d in FUNCTION_DIRS]

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
    """Structure names (file names without .nbt) of model `name` in directory."""
    file_list = []
    if os.path.exists(directory):
        for filename in sorted(os.listdir(directory)):
            if _is_model_file(filename, name, ".nbt") and "_" in filename:
                file_list.append(filename[:-len(".nbt")])
    else:
        print(f"Directory {directory} does not exist.")
    df = pd.DataFrame({"group": file_list})
    return df


def find_delete_nbt(directory, name):
    file_list = []
    for filename in sorted(os.listdir(directory)):
        if _is_model_file(filename, "delete_" + name, ".nbt"):
            file_list.append(filename[:-len(".nbt")])
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

    dirs = structure_dirs(directory)

    # iterate through each line in functions
    for line in functions:
        block_type = line.split(' ')[4]
        block_type = str(block_type.split(':')[1])
        x = int(line.split(' ')[1].split('~')[1])
        y = int(line.split(' ')[2].split('~')[1])
        z = int(line.split(' ')[3].split('~')[1])
        nbtstructure.set_block(Vector(x, y, z), BlockData(block_type))

    nbt_file = os.path.join(dirs[0], f"{pdb_name}.nbt")
    nbtstructure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)
    _mirror_files([nbt_file], dirs[0], dirs)


def _write_structure(coords, block_types, path):
    nbtstructure = NBTStructure()
    for (x, y, z), block in zip(coords, block_types):
        nbtstructure.set_block(Vector(int(x), int(y), int(z)), BlockData(block))
    nbtstructure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=path)
    return path


def process_nbt_chunk(chunk, block_dict, air, dir, name, idx, delete_too=False):
    """
    Write one <name>_part<idx>.nbt into dir; with delete_too also the matching all-air
    delete_<name>_part<idx>.nbt used by the clear_ function. Returns the written paths.
    """
    # np.array copies: under pandas copy-on-write, .values is read-only and += would fail
    coords = np.array(chunk[['X', 'Y', 'Z']].to_numpy(dtype=float).round(), dtype=int)
    coords[:, 0] += 40
    coords[:, 2] += 40

    if 'atom' in chunk.columns:
        atoms = chunk['atom'].astype(str).to_numpy()
        if isinstance(block_dict, str):
            block_types = np.full(len(chunk), block_dict, dtype=object)
        else:
            # one lookup per distinct label rather than per block
            labels, inverse = np.unique(atoms, return_inverse=True)
            block_types = np.array([_block_for_atom(a, block_dict) for a in labels], dtype=object)[inverse]
    else:
        block_types = np.full(len(chunk), block_dict.get('backbone_atom', 'pink_concrete'), dtype=object)

    if air:
        block_types[:] = 'air'

    paths = [_write_structure(coords, block_types, os.path.join(dir, f"{name.lower()}_part{idx}.nbt"))]
    if delete_too and not air:
        paths.append(_write_structure(coords, np.full(len(coords), 'air', dtype=object),
                                      os.path.join(dir, f"delete_{name.lower()}_part{idx}.nbt")))
    return paths


def create_nbt(df, name, air, dir, blocks, num_threads=4):
    """
    Write df (X, Y, Z[, atom]) as up to num_threads structure parts <name>_part<i>.nbt, plus the matching
    delete_ structures, into every structure folder of the world. dir is the datapack functions folder.
    Errors are raised rather than silently lost in the worker threads.
    """
    dirs = structure_dirs(dir)
    if df is None or df.empty:
        return []
    # One block per position. Later rows win, matching the order the parts are placed in game
    df = df.drop_duplicates(subset=['X', 'Y', 'Z'], keep='last')
    # Split by row position (np.array_split on a DataFrame no longer works with pandas 3)
    bounds = np.linspace(0, len(df), min(num_threads, len(df)) + 1).astype(int)
    chunks = [df.iloc[start:end] for start, end in zip(bounds[:-1], bounds[1:]) if end > start]
    results = _run_all([(process_nbt_chunk, chunk, blocks, air, dirs[0], name, idx, True)
                        for idx, chunk in enumerate(chunks)], max_workers=num_threads)
    written = [p for paths in results for p in paths]
    _mirror_files(written, dirs[0], dirs)
    return written


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
            f.write(f'place template {STRUCTURE_NAMESPACE}:{item}\n')
    return [os.path.join(directory, f"build_{lower_pdb_name}.mcfunction")]


def create_individual_nbt_functions(mcfiles, directory):
    mcfiles_list = mcfiles.values.flatten().tolist()
    written = []
    for file in mcfiles_list:
        basename = os.path.splitext(file)[0]
        path = os.path.join(directory, f"build_{basename}.mcfunction")
        with open(path, 'w') as f:
            f.write(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
            f.write(f'say Loading {basename}... please wait. May take some time.\n')
            f.write(f'place template {STRUCTURE_NAMESPACE}:{file}\n')
        written.append(path)
    return written


def process_nbt_file(nbt_dir, filename):
    nbt_structure = NBTStructure(os.path.join(nbt_dir, filename))
    for block in nbt_structure.blocks:
        nbt_structure.set_block(block, BlockData('air'))
    nbt_file = os.path.join(nbt_dir, f"delete_{filename}")
    nbt_structure.get_nbt(pressurize=False, align_to_origin=False).write_file(filename=nbt_file)
    return nbt_file


def create_nbt_delete(pdb_name, mc_dir):
    """
    Make the all-air delete_<structure>.nbt for each structure of the model. create_nbt already writes
    these alongside each part, so only structures without an up-to-date delete_ file are converted.
    """
    dirs = structure_dirs(mc_dir)
    nbt_dir = dirs[0]
    lower_pdb_name = pdb_name.lower()

    files = []
    for filename in os.listdir(nbt_dir):
        if not _is_model_file(filename, lower_pdb_name, ".nbt"):
            continue
        delete_path = os.path.join(nbt_dir, f"delete_{filename}")
        if (os.path.exists(delete_path) and
                os.path.getmtime(delete_path) >= os.path.getmtime(os.path.join(nbt_dir, filename))):
            continue
        files.append(filename)

    written = _run_all([(process_nbt_file, nbt_dir, filename) for filename in files])
    _mirror_files(written, nbt_dir, dirs)


def create_nbt_delete_function(mcfiles, pdb_name, directory):
    lower_pdb_name = pdb_name.lower()

    # sort df by the naming convention
    mcfiles['group'] = mcfiles['group'].astype(str)
    mcfiles = mcfiles.sort_values('group', key=lambda x: x.str.split('_').str[1])

    with open(os.path.join(directory, f"clear_{lower_pdb_name}.mcfunction"), 'w') as f:
        f.write(f'say Removing... must be standing on original obsidian block.\n')
        for item in mcfiles['group']:
            f.write(f'place template {STRUCTURE_NAMESPACE}:{item}\n')
    return [os.path.join(directory, f"clear_{lower_pdb_name}.mcfunction")]


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
        dirs = structure_dirs(directory)
        nbt_dir = dirs[0]

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
        _mirror_files([os.path.join(nbt_dir, f) for f in files], nbt_dir, dirs)


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
    """Write the build function(s) for the model's structures into both datapack function folders."""
    nbt_dir = structure_dirs(mc_dir)[0]
    mcfiles = find_nbt(nbt_dir, pdb_name.lower())

    os.makedirs(mc_dir, exist_ok=True)
    if config_data["simple"]:
        written = create_nbt_function(mcfiles, pdb_name, mc_dir)
    else:
        written = create_individual_nbt_functions(mcfiles, mc_dir)

    # Only this model's functions are copied to the 1.21+ "function" folder
    _mirror_files(written, os.path.normpath(mc_dir), function_dirs(mc_dir))


def finish_delete_nbts(mc_dir, pdb_name):
    """Write clear_<name>.mcfunction, which places the all-air structures, into both function folders."""
    nbt_dir = structure_dirs(mc_dir)[0]

    mcfiles = find_delete_nbt(nbt_dir, pdb_name.lower())

    written = create_nbt_delete_function(mcfiles, pdb_name, mc_dir)

    _mirror_files(written, os.path.normpath(mc_dir), function_dirs(mc_dir))
