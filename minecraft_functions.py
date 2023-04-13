import pandas as pd
import os
import glob

def create_minecraft_functions(df, name, air, dir):
    block_dict = {'C': 'black_concrete', 'N': 'blue_concrete', 'O': 'red_concrete',
                  'H': 'white_concrete', 'S': 'yellow_concrete'}
    block_type = 'air' if air else 'block'
    functions = []
    name = name.lower()
    for index, row in df.iterrows():
        x, y, z = row['X'], row['Y'], row['Z']
        if 'atom' in df.columns:
            block = block_dict.get(row['atom'], 'pink_concrete')
        else:
            block = 'gray_concrete'
        if air:
            block = 'air'
        x += 100
        y += 100
        z += 100
        function = f'setblock ~{x} ~{y} ~{z} minecraft:{block}\n'
        functions.append(function)

    num_files = (len(functions) // 10000) + 1
    for i in range(num_files):
        file_num = i + 1
        filename = f"{name}_{file_num}_{block_type}.mcfunction"
        filepath = os.path.join(dir, filename)
        start = i * 10000
        end = start + 10000
        with open(filepath, 'w') as f:
            f.writelines(functions[start:end])

def find_mcfunctions(directory, name):
    file_list = []
    for filename in os.listdir(directory):
        if filename.startswith(name) and filename.endswith(".mcfunction"):
            parts = filename.split("_")
            full = filename.split(".")
            if len(parts) > 1:
                file_list.append(full[0])
    df = pd.DataFrame({"group": file_list})
    return df

def create_master_function(df, name, directory):
    name = name.lower()
    # sort df by the naming convention
    df = df.sort_values('group', key=lambda x: x.str.split('_').str[1])
    # create a list of commands to execute each mcfunction in order
    commands = [f'function protein:{x}' for x in df['group']]
    print(len(commands))
    # create a make_{name}.mcfunction file with the commands
    with open(os.path.join(directory, f"make_{name}.mcfunction"), 'w') as f:
        for i in range(0, len(commands)):
            f.write(f'{commands[i]}\n')
    with open(os.path.join(directory, f"drop_{name}.mcfunction"), 'w') as f:
        f.write(f'setblock ~ ~ ~ minecraft:command_block{{Command:"function protein:make_{name}"}}\n')
        f.write(f'setblock ~ ~ ~1 minecraft:stone_button[facing=south,powered=false]')
