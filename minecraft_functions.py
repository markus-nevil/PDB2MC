import pandas as pd
import os
import variables
import glob


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


def delete_mcfunctions(directory, name):
    for filename in os.listdir(directory):
        if filename.startswith(name) and filename.endswith(".mcfunction"):
            os.remove(os.path.join(directory, filename))


def find_mcfunctions(directory, name):
    file_list = []
    for filename in os.listdir(directory):
        if filename.startswith("z"+name) and filename.endswith(".mcfunction"):
            parts = filename.split("_")
            full = filename.split(".")
            if len(parts) > 1:
                file_list.append(full[0])
    df = pd.DataFrame({"group": file_list})
    print(df)
    return df

def create_clear_function(mc_dir, pdb_name):
    # find all files in the directory that start with "z" + pdb_name and copy all the lines into a list
    functions = []
    pdb_name = pdb_name.lower()

    for filename in os.listdir(mc_dir):
        if filename.startswith("z" + pdb_name) and filename.endswith(".mcfunction"):
            with open(os.path.join(mc_dir, filename), 'r') as f:
                #skip any lines that start with setblock ~ ~-1 ~
                functions += [x for x in f.readlines() if not x.startswith("setblock ~ ~-1 ~")]


    for i in range(len(functions)):
        if 'minecraft' in functions[i]:
            functions[i] = functions[i].split('minecraft', 1)[0] + 'minecraft:air replace\n'

    #remove duplicate lines
    functions = list(dict.fromkeys(functions))

    # create a clear_{name}.mcfunction file with the commands
    with open(os.path.join(mc_dir, f"clear_{pdb_name}.mcfunction"), 'w') as f:
        #f.write('execute as @a[scores={}] run teleport @s[scores={X=1.., Y=1.., Z=1..}] ~ ~ ~\n')
        f.writelines(functions)

def create_master_function(df, name, directory):
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
        f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')
        #f.write(f'summon armor_stand ~ ~ ~ {Invisible:true, Invulnerable:true, CustomName:'"{name}"', CustomNameVisible:false, ShowArms:false} ')

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
        f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')
        f.write(f'setblock ~ ~-1 ~ minecraft:obsidian replace\n')
        f.writelines(functions)


def adjust_y_coords(directory, pdb_name):
    min_y = None
    files = []

    print(directory)
    # Find the minimum Y value
    for filename in os.listdir(directory):
        if pdb_name in filename and filename.endswith(".mcfunction"):
            print(filename)
            files.append(filename)
            with open(os.path.join(directory, filename), 'r') as f:
                for line in f:
                    if not line.startswith("setblock ~ ~-1 ~ minecraft:obsidian replace") and 'setblock' in line:
                        y = int(float(line.split(' ~')[2]))
                        if min_y is None or y < min_y:
                            min_y = y

    # Adjust Y values in the files
    for filename in files:
        with open(os.path.join(directory, filename), 'r') as f:
            lines = f.readlines()
        with open(os.path.join(directory, filename), 'w') as f:
            for line in lines:
                if not line.startswith("setblock ~ ~-1 ~ minecraft:obsidian replace") and 'setblock' in line:
                    y = int(float(line.split(' ~')[2]))
                    adjusted_y = y - min_y

                    ##TODO I think this needs to be split by spaces like line.split(' ')[0:2] to grab the first bit.
                    #test = tl.split(' ')[0:2].unlist() + " ~" + str(555) + tl.split(' ')[4:5].unlist()
                    line = line.split(' ~')[0] + ' ~' + str(adjusted_y) + line.split(' ~')[3]

                f.write(line)
