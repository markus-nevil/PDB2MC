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
    with open(os.path.join(directory, f"make_{name}.mcfunction"), 'w') as f:
        f.write(f'gamerule maxCommandChainLength 1000000\n')
        f.write(f'tp @s ~ ~ ~ facing {first_block[0]} {first_block[1]} {first_block[2]}\n')
        for i in range(0, len(commands)):
            f.write(f'{commands[i]}\n')